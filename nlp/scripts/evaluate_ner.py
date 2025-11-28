"""
Evaluate trained NER model on test set

Calculates Precision, Recall, F1 scores per entity type and overall.

Usage:
    python nlp/scripts/evaluate_ner.py
"""

import spacy
from spacy.training import Example
from spacy.scorer import Scorer
from pathlib import Path
import json
from datetime import datetime


def evaluate_ner_model():
    """Evaluate NER model and save results"""
    
    print("=" * 80)
    print("📊 NER Model Evaluation")
    print("=" * 80)
    
    # Paths
    model_path = Path(__file__).parent.parent / "models" / "ner_model" / "model-best"
    test_data_path = Path(__file__).parent.parent / "training_data" / "spacy" / "dev.spacy"
    output_path = Path(__file__).parent.parent / "evaluation" / "ner_evaluation_results.json"
    
    print(f"\n📦 Loading model from: {model_path}")
    print(f"📄 Loading test data from: {test_data_path}\n")
    
    # Load model
    try:
        nlp = spacy.load(model_path)
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Load test data
    try:
        from spacy.tokens import DocBin
        doc_bin = DocBin().from_disk(test_data_path)
        test_docs = list(doc_bin.get_docs(nlp.vocab))
        print(f"✅ Loaded {len(test_docs)} test documents\n")
    except Exception as e:
        print(f"❌ Error loading test data: {e}")
        return
    
    print("=" * 80)
    print("🧮 Computing Scores...")
    print("=" * 80)
    
    # Create examples for scoring
    examples = []
    for gold_doc in test_docs:
        # Predict on the text
        pred_doc = nlp(gold_doc.text)
        # Create Example object
        example = Example(pred_doc, gold_doc)
        examples.append(example)
    
    # Compute scores
    scorer = Scorer()
    scores = scorer.score(examples)
    
    # Extract NER-specific scores
    ner_scores = scores.get("ents_per_type", {})
    overall_scores = {
        "precision": scores.get("ents_p", 0),
        "recall": scores.get("ents_r", 0),
        "f1": scores.get("ents_f", 0)
    }
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 Overall NER Performance")
    print("=" * 80)
    print(f"Precision: {overall_scores['precision']:.4f} ({overall_scores['precision']*100:.2f}%)")
    print(f"Recall:    {overall_scores['recall']:.4f} ({overall_scores['recall']*100:.2f}%)")
    print(f"F1 Score:  {overall_scores['f1']:.4f} ({overall_scores['f1']*100:.2f}%)")
    
    print("\n" + "=" * 80)
    print("📈 Per-Entity Type Performance")
    print("=" * 80)
    
    # Sort entity types for consistent display
    entity_types = sorted(ner_scores.keys())
    
    print(f"\n{'Entity Type':<15} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("─" * 80)
    
    per_type_results = {}
    for ent_type in entity_types:
        type_scores = ner_scores[ent_type]
        p = type_scores.get("p", 0)
        r = type_scores.get("r", 0)
        f = type_scores.get("f", 0)
        
        per_type_results[ent_type] = {
            "precision": p,
            "recall": r,
            "f1": f
        }
        
        print(f"{ent_type:<15} {p:>6.2%}       {r:>6.2%}       {f:>6.2%}")
    
    # Performance assessment
    print("\n" + "=" * 80)
    print("✅ Performance Assessment")
    print("=" * 80)
    
    f1_score = overall_scores['f1']
    if f1_score >= 0.85:
        status = "✅ EXCELLENT"
        message = "Model exceeds target performance (≥85%)"
    elif f1_score >= 0.75:
        status = "✅ GOOD"
        message = "Model meets minimum target (≥75%)"
    elif f1_score >= 0.65:
        status = "⚠️  ACCEPTABLE"
        message = "Model performance is acceptable but could be improved"
    else:
        status = "❌ NEEDS IMPROVEMENT"
        message = "Model performance is below acceptable threshold"
    
    print(f"\nStatus: {status}")
    print(f"F1 Score: {f1_score*100:.2f}%")
    print(f"Assessment: {message}")
    
    # Save results
    results = {
        "evaluation_date": datetime.now().isoformat(),
        "model_path": str(model_path),
        "test_data_path": str(test_data_path),
        "num_test_examples": len(test_docs),
        "overall_scores": overall_scores,
        "per_type_scores": per_type_results,
        "status": status,
        "message": message
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_path}")
    
    print("\n" + "=" * 80)
    print("✅ Evaluation Complete!")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    evaluate_ner_model()
