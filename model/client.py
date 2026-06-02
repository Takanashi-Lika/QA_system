"""Model 客户端 — 统一的 LLM 文本生成调用模块。

兼容 OpenAI SDK 格式（DeepSeek / Ollama / vLLM 等均可接入）。
提供同步/流式对话、提示词模板、指数退避重试与异常分层处理。

配置方式（按优先级）:
  1. 直接设置类属性   client.model_name = "deepseek-v4-pro"
  2. 环境变量         MODEL_BASE_URL / MODEL_API_KEY / MODEL_NAME ...
  3. 代码默认值
"""

import os
import time
import logging
from typing import Generator

from openai import OpenAI

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 自定义异常 — 分层处理，调用方可以按类型 catch
# ---------------------------------------------------------------------------


class ModelError(Exception):
    """Model 模块所有异常的基类"""
    pass


class ModelTimeoutError(ModelError):
    """请求超时"""
    pass


class ModelRateLimitError(ModelError):
    """请求限流（429），重试后仍未恢复"""
    pass


class ModelAPIError(ModelError):
    """API 返回的错误（非超时、非限流）"""
    pass


# ---------------------------------------------------------------------------
# ModelClient
# ---------------------------------------------------------------------------


class ModelClient:
    """统一的 LLM 调用客户端。

    属性（可直接赋值覆盖默认值）:
        base_url:    API 端点地址
        api_key:     API 密钥
        model_name:  模型名称
        max_retries: 最大重试次数
        timeout:     单次请求超时秒数

    使用方式:
        client = ModelClient()
        client.base_url = "https://api.deepseek.com/v1"
        client.api_key = "your-api-key-here"
        response = client.chat([{"role": "user", "content": "你好"}])
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
        max_retries: int | None = None,
        timeout: int | None = None,
    ):
        # 属性配置：构造参数 > 环境变量 > 硬编码默认值
        self.base_url = base_url or os.getenv("MODEL_BASE_URL", "https://api.deepseek.com/v1")
        self.api_key = api_key or os.getenv("MODEL_API_KEY", "your-api-key-here")
        self.model_name = model_name or os.getenv("MODEL_NAME", "deepseek-v4-pro")
        self.max_retries = max_retries or int(os.getenv("MODEL_MAX_RETRIES", "3"))
        self.timeout = timeout or int(os.getenv("MODEL_TIMEOUT", "60"))

        self._client: OpenAI | None = None

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    @property
    def client(self) -> OpenAI:
        """懒加载 OpenAI 兼容客户端（属性变更后自动重建）。"""
        if self._client is None:
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
            )
        return self._client

    def _reset_client(self):
        """属性变更后清除缓存，下次调用时重建。"""
        self._client = None

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        # 当关键属性被修改时，让下次 client 访问重建连接
        if name in ("base_url", "api_key", "timeout"):
            super().__setattr__("_client", None)

    # ------------------------------------------------------------------
    # 同步对话
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
    ) -> str:
        """同步对话，带指数退避重试。

        Args:
            messages:    OpenAI 格式消息列表 [{"role": "user", "content": "..."}]
            temperature: 生成温度（0~2），越低越确定

        Returns:
            模型回复的文本内容

        Raises:
            ModelTimeoutError:  超时且重试耗尽
            ModelRateLimitError: 限流且重试耗尽
            ModelAPIError:      其他 API 错误
        """
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                )
                return response.choices[0].message.content or ""

            except Exception as e:
                error_msg = str(e)

                # 超时
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    if attempt < self.max_retries:
                        delay = _backoff_delay(attempt)
                        logger.warning("请求超时，%d/%d 次重试，等待 %.1fs", attempt + 1, self.max_retries, delay)
                        time.sleep(delay)
                        continue
                    raise ModelTimeoutError(f"请求超时，已重试 {self.max_retries} 次: {error_msg}") from e

                # 限流 (HTTP 429)
                if "429" in error_msg or "rate" in error_msg.lower():
                    if attempt < self.max_retries:
                        delay = _backoff_delay(attempt)
                        logger.warning("请求限流，%d/%d 次重试，等待 %.1fs", attempt + 1, self.max_retries, delay)
                        time.sleep(delay)
                        continue
                    raise ModelRateLimitError(f"请求限流，已重试 {self.max_retries} 次: {error_msg}") from e

                # 其他 API 错误不重试
                raise ModelAPIError(f"API 调用失败: {error_msg}") from e

        # 理论上不会到这里
        raise ModelError("未知错误")

    # ------------------------------------------------------------------
    # 流式对话
    # ------------------------------------------------------------------

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
    ) -> Generator[str, None, None]:
        """流式对话，逐 token yield 文本。

        用法:
            for chunk in client.chat_stream(messages):
                print(chunk, end="")
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            raise ModelAPIError(f"流式调用失败: {e}") from e

    # ------------------------------------------------------------------
    # 提示词模板
    # ------------------------------------------------------------------

    @staticmethod
    def format_prompt(template: str, **kwargs) -> str:
        """用 {key} 占位符填充模板。

        Example:
            tpl = "你是{role}，请回答: {question}"
            client.format_prompt(tpl, role="客服", question="怎么退货")
            # → "你是客服，请回答: 怎么退货"
        """
        return template.format(**kwargs)


# ---------------------------------------------------------------------------
# 模块级单例
# ---------------------------------------------------------------------------

_model_client: ModelClient | None = None


def get_model_client() -> ModelClient:
    """获取 ModelClient 模块级单例。

    首次调用时从环境变量初始化，后续调用返回同一实例。
    如需修改配置，直接设置实例属性即可。
    """
    global _model_client
    if _model_client is None:
        _model_client = ModelClient()
    return _model_client


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _backoff_delay(attempt: int, base: float = 2.0, max_delay: float = 30.0) -> float:
    """指数退避：2^attempt ± 随机抖动，上限 max_delay 秒。"""
    return min(base ** attempt + (time.time() % 1), max_delay)
