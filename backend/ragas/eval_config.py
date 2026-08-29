from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

CONFIG_PATH = Path(__file__).with_name("eval_config.json")


def load_eval_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_active_template_name(config: dict[str, Any]) -> str:
    template_name = config.get("active_template", "standard")
    templates = config.get("templates", {})
    if template_name not in templates:
        available = ", ".join(sorted(templates))
        raise ValueError(f"未找到评测模板: {template_name}，可选模板: {available}")
    return template_name


def build_metrics(config: dict[str, Any]) -> list:
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    metric_registry = {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_precision": context_precision,
        "context_recall": context_recall,
    }

    try:
        from ragas.metrics import answer_correctness
        metric_registry["answer_correctness"] = answer_correctness
    except ImportError:
        pass

    template_name = get_active_template_name(config)
    metric_names = config["templates"][template_name].get("metrics", [])

    metrics = []
    missing: list[str] = []
    for metric_name in metric_names:
        metric = metric_registry.get(metric_name)
        if metric is None:
            missing.append(metric_name)
            continue
        metrics.append(metric)

    if missing:
        raise ValueError(
            "以下指标当前不可用或未安装: " + ", ".join(missing)
        )

    if not metrics:
        raise ValueError(f"评测模板 {template_name} 未配置任何可用指标")

    return metrics


def build_evaluator_llm(config: dict[str, Any]) -> ChatOpenAI:
    llm_config = config.get("llm", {})
    api_key = os.getenv(llm_config.get("api_key_env", "OPENAI_API_KEY"))

    # 评测模型独立配置：RAGAS_LLM_MODEL / RAGAS_LLM_BASE_URL 优先，
    # 其次使用 eval_config.json 的配置（与项目服务的 LLM_MODEL 互不影响）
    model = os.getenv("RAGAS_LLM_MODEL") or llm_config.get("model", "qwen-max")
    base_url = os.getenv("RAGAS_LLM_BASE_URL") or llm_config.get("base_url")

    return ChatOpenAI(
        api_key=api_key,
        model=model,
        base_url=base_url,
        temperature=llm_config.get("temperature", 0),
    )


def build_evaluator_embeddings(config: dict[str, Any]) -> HuggingFaceEmbeddings:
    embeddings_config = config.get("embeddings", {})
    return HuggingFaceEmbeddings(
        model_name=embeddings_config.get("model_name", "BAAI/bge-small-zh-v1.5")
    )


def get_knowledge_base_id_env(config: dict[str, Any]) -> str:
    retrieval_config = config.get("retrieval", {})
    return retrieval_config.get("knowledge_base_id_env", "RAGAS_KB_ID")
