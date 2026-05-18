import argparse
import sys
import os
# Allow imports from the same directory (src)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import InferenceEngine

def main():
    parser = argparse.ArgumentParser(
        description="Forward Chaining Chemical Inference Engine — Production CLI"
    )
    parser.add_argument(
        "--kb", 
        type=str, 
        default=os.path.join(os.path.dirname(__file__), "knowledge_base.json"), 
        help="Path to the JSON Knowledge Base file"
    )
    parser.add_argument(
        "--facts", 
        type=str, 
        nargs="+", 
        required=True, 
        help="List of initial facts (starting chemicals) separated by spaces. Example: Na H2O"
    )
    parser.add_argument(
        "--goal", 
        type=str, 
        default=None, 
        help="Target chemical product to deduce/synthesize. Example: NaOH"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.kb):
        print(f"[FATAL ERROR] Knowledge Base not found at path: {args.kb}")
        sys.exit(1)
        
    print(f"[AIE INFO] Initializing Inference Engine using Knowledge Base: {args.kb}")
    engine = InferenceEngine(args.kb)
    
    print(f"[AIE INFO] Working Memory Initialized with Facts: {args.facts}")
    if args.goal:
        print(f"[AIE INFO] Target Synthesis Goal: {args.goal}")
        
    print("\n[AIE INFO] Initiating Forward Chaining Inference Strategy...\n")
    
    result = engine.forward_chaining(args.facts, args.goal)
    
    if args.goal:
        if result["goal_reached"]:
            print(f"✅ SUCCESS: Synthesis of '{args.goal}' is feasible from the given initial reactants.")
            print(f"Reaction Path (Triggered Rules Sequence): {' -> '.join(result['path'])}")
        else:
            print(f"❌ FAILURE: Unable to synthesize '{args.goal}' with the current Knowledge Base rules.")
    else:
        print("✅ SUCCESS: Forward inference process completed successfully.")
        print(f"Triggered Rules Sequence: {result['path']}")
        
    print(f"\nFinal State of Working Memory (All Known Facts): {', '.join(result['known_facts'])}")

if __name__ == "__main__":
    main()
