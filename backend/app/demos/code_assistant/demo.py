# demo.py
from orchestrator import orchestrator

def demo_simple_explanation():
    """Demo: Simple code explanation"""
    print("\n" + "="*60)
    print("DEMO 1: Simple Explanation")
    print("="*60)
    
    sample_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    orchestrator(
        user_request="What does this code do?",
        code=sample_code,
        stream=True
    )


def demo_production_ready():
    """Demo: Make code production-ready (refactor + document)"""
    print("\n" + "="*60)
    print("DEMO 2: Production-Ready Transformation")
    print("="*60)
    
    messy_code = """
def calc(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        return a / b
"""
    
    orchestrator(
        user_request="Make this production-ready with proper documentation",
        code=messy_code,
        stream=True
    )


def demo_refactor_focus():
    """Demo: Focused refactoring"""
    print("\n" + "="*60)
    print("DEMO 3: Refactor for Readability")
    print("="*60)
    
    nested_code = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            if item % 2 == 0:
                if item < 100:
                    result.append(item * 2)
    return result
"""
    
    orchestrator(
        user_request="Refactor this to reduce nesting and improve readability",
        code=nested_code,
        stream=True
    )


def demo_full_analysis():
    """Demo: Complete analysis with all agents"""
    print("\n" + "="*60)
    print("DEMO 4: Full Code Analysis")
    print("="*60)
    
    code = """
def sort_list(lst):
    for i in range(len(lst)):
        for j in range(i+1, len(lst)):
            if lst[i] > lst[j]:
                lst[i], lst[j] = lst[j], lst[i]
    return lst
"""
    
    orchestrator(
        user_request="Analyze this code completely - explain, refactor, and document it",
        code=code,
        stream=True
    )


def demo_custom_request():
    """Demo: Custom user request"""
    print("\n" + "="*60)
    print("DEMO 5: Custom Request")
    print("="*60)
    
    code = input("\nPaste your code (press Enter then Ctrl+D when done):\n")
    request = input("\nWhat would you like me to do with it?\n> ")
    
    orchestrator(
        user_request=request,
        code=code,
        stream=True
    )


def run_all_demos():
    """Run all demos sequentially"""
    demo_simple_explanation()
    input("\nPress Enter to continue to next demo...")
    
    demo_production_ready()
    input("\nPress Enter to continue to next demo...")
    
    demo_refactor_focus()
    input("\nPress Enter to continue to next demo...")
    
    demo_full_analysis()
    print("\n✅ All demos completed!")


if __name__ == "__main__":
    print("\n🧠 PROJECT 29: Code Analysis Multi-Agent System")
    print("="*60)
    print("\nAvailable Demos:")
    print("1. Simple Explanation")
    print("2. Production-Ready Transformation")
    print("3. Refactor for Readability")
    print("4. Full Code Analysis")
    print("5. Custom Request (Interactive)")
    print("6. Run All Demos")
    print("="*60)
    
    choice = input("\nSelect demo (1-6): ").strip()
    
    if choice == "1":
        demo_simple_explanation()
    elif choice == "2":
        demo_production_ready()
    elif choice == "3":
        demo_refactor_focus()
    elif choice == "4":
        demo_full_analysis()
    elif choice == "5":
        demo_custom_request()
    elif choice == "6":
        run_all_demos()
    else:
        print("Invalid choice. Running Demo 1 by default...")
        demo_simple_explanation()