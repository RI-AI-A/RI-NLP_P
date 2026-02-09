"""Offline Evaluation Pipeline"""
import asyncio
import csv
import json
from typing import List, Dict, Any
from pathlib import Path
from nlp_service.intent_classifier import get_intent_classifier
from nlp_service.slot_filling import get_slot_filler
import structlog

logger = structlog.get_logger()


class EvaluationMetrics:
    """Calculate evaluation metrics"""
    
    @staticmethod
    def intent_accuracy(predictions: List[str], ground_truth: List[str]) -> float:
        """Calculate intent classification accuracy"""
        if not predictions or not ground_truth:
            return 0.0
        
        correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
        return correct / len(predictions)
    
    @staticmethod
    def slot_f1(predicted_slots: List[Dict], true_slots: List[Dict]) -> float:
        """
        Calculate F1 score for slot extraction
        
        Simplified version - compares slot keys
        """
        if not predicted_slots or not true_slots:
            return 0.0
        
        total_precision = 0.0
        total_recall = 0.0
        
        for pred, true in zip(predicted_slots, true_slots):
            pred_keys = set(pred.keys())
            true_keys = set(true.keys())
            
            if not pred_keys and not true_keys:
                precision = 1.0
                recall = 1.0
            elif not pred_keys:
                precision = 0.0
                recall = 0.0
            elif not true_keys:
                precision = 0.0
                recall = 0.0
            else:
                tp = len(pred_keys & true_keys)
                precision = tp / len(pred_keys) if pred_keys else 0.0
                recall = tp / len(true_keys) if true_keys else 0.0
            
            total_precision += precision
            total_recall += recall
        
        avg_precision = total_precision / len(predicted_slots)
        avg_recall = total_recall / len(predicted_slots)
        
        if avg_precision + avg_recall == 0:
            return 0.0
        
        f1 = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall)
        return f1
    
    @staticmethod
    def confidence_calibration(confidences: List[float], correct: List[bool]) -> Dict[str, float]:
        """
        Calculate confidence calibration metrics
        
        Returns expected calibration error (ECE)
        """
        if not confidences or not correct:
            return {"ece": 0.0}
        
        # Simple binning approach
        n_bins = 10
        bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
        
        bin_accuracies = []
        bin_confidences = []
        bin_counts = []
        
        for i in range(n_bins):
            lower = bin_boundaries[i]
            upper = bin_boundaries[i + 1]
            
            # Find samples in this bin
            in_bin = [(c, cor) for c, cor in zip(confidences, correct) 
                     if lower <= c < upper or (i == n_bins - 1 and c == upper)]
            
            if in_bin:
                bin_counts.append(len(in_bin))
                bin_confidences.append(sum(c for c, _ in in_bin) / len(in_bin))
                bin_accuracies.append(sum(1 for _, cor in in_bin if cor) / len(in_bin))
            else:
                bin_counts.append(0)
                bin_confidences.append(0)
                bin_accuracies.append(0)
        
        # Calculate ECE
        total_samples = len(confidences)
        ece = sum(
            (count / total_samples) * abs(acc - conf)
            for count, acc, conf in zip(bin_counts, bin_accuracies, bin_confidences)
            if count > 0
        )
        
        return {"ece": ece}


async def evaluate_from_csv(input_path: str, output_path: str = None):
    """
    Run offline evaluation from CSV file
    
    CSV format:
    query,true_intent,true_slots (JSON string)
    
    Args:
        input_path: Path to CSV file with labeled data
        output_path: Path to save evaluation report (JSON)
    """
    logger.info("Starting offline evaluation", input_path=input_path)
    
    # Load data
    queries = []
    true_intents = []
    true_slots_list = []
    
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries.append(row['query'])
            true_intents.append(row['true_intent'])
            true_slots_list.append(json.loads(row.get('true_slots', '{}')))
    
    logger.info("Loaded evaluation data", count=len(queries))
    
    # Initialize models
    intent_classifier = get_intent_classifier()
    slot_filler = get_slot_filler()
    
    # Run predictions
    predicted_intents = []
    predicted_slots_list = []
    confidences = []
    
    for query, true_intent in zip(queries, true_intents):
        # Predict intent
        intent, confidence = await intent_classifier.predict(query)
        predicted_intents.append(intent)
        confidences.append(confidence)
        
        # Extract slots
        slots = await slot_filler.extract_slots(query, intent)
        predicted_slots_list.append(slots)
    
    # Calculate metrics
    metrics = EvaluationMetrics()
    
    intent_acc = metrics.intent_accuracy(predicted_intents, true_intents)
    slot_f1 = metrics.slot_f1(predicted_slots_list, true_slots_list)
    
    correct_predictions = [p == t for p, t in zip(predicted_intents, true_intents)]
    calibration = metrics.confidence_calibration(confidences, correct_predictions)
    
    rejection_rate = sum(1 for i in predicted_intents if i == "unknown") / len(predicted_intents)
    
    # Resolution rate (queries with valid intent and required slots)
    resolution_count = 0
    for intent, slots in zip(predicted_intents, predicted_slots_list):
        if intent != "unknown":
            # Check if required slots are present (simplified)
            if intent == "kpi_query" and "branch_id" in slots:
                resolution_count += 1
            elif intent in ["branch_status"] and "branch_id" in slots:
                resolution_count += 1
            elif intent in ["task_management", "event_query", "promotion_query", "chitchat"]:
                resolution_count += 1
    
    resolution_rate = resolution_count / len(queries)
    
    # Build report
    report = {
        "evaluation_date": "2026-02-08",
        "dataset_size": len(queries),
        "metrics": {
            "intent_accuracy": round(intent_acc, 4),
            "slot_f1": round(slot_f1, 4),
            "confidence_calibration_ece": round(calibration["ece"], 4),
            "rejection_rate": round(rejection_rate, 4),
            "query_resolution_rate": round(resolution_rate, 4)
        },
        "per_intent_accuracy": {}
    }
    
    # Per-intent accuracy
    for intent in set(true_intents):
        intent_mask = [t == intent for t in true_intents]
        intent_preds = [p for p, m in zip(predicted_intents, intent_mask) if m]
        intent_true = [t for t, m in zip(true_intents, intent_mask) if m]
        
        if intent_preds:
            intent_acc = sum(1 for p, t in zip(intent_preds, intent_true) if p == t) / len(intent_preds)
            report["per_intent_accuracy"][intent] = round(intent_acc, 4)
    
    logger.info("Evaluation completed", metrics=report["metrics"])
    
    # Save report
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info("Evaluation report saved", output_path=output_path)
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python evaluation.py <input_csv> [output_json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "evaluation_report.json"
    
    asyncio.run(evaluate_from_csv(input_file, output_file))
