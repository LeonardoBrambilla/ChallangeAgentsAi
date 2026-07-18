"""Avaliação automatizada (prompt-eval) do RagAgent via ragas.

Roda cada pergunta do dataset contra o agente de RAG real (Chroma + Azure OpenAI já
ingeridos), coleta resposta + contexto recuperado, e mede faithfulness/answer_relevancy/
context_precision/context_recall contra o ground_truth esperado.

Uso:
    python -m eval.run_eval
"""
import json
from pathlib import Path

from datasets import Dataset
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

from agents.rag_agent import run_rag_agent
from llm_factory import get_chat_llm, get_embeddings

DATASET_PATH = Path(__file__).parent / "dataset.json"


def build_ragas_dataset() -> Dataset:
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    questions, answers, contexts, ground_truths = [], [], [], []
    for case in cases:
        answer, rag_result = run_rag_agent(case["question"])
        questions.append(case["question"])
        answers.append(answer)
        contexts.append(rag_result.chunks or [""])
        ground_truths.append(case["ground_truth"])

    return Dataset.from_dict(
        {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
    )


def main() -> None:
    dataset = build_ragas_dataset()

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=LangchainLLMWrapper(get_chat_llm()),
        embeddings=LangchainEmbeddingsWrapper(get_embeddings()),
    )

    print("\n=== Resultado da avaliação (ragas) ===")
    print(result)


if __name__ == "__main__":
    main()
