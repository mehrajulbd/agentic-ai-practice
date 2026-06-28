from general_qs import handle_general_query
from refund import handle_refund
from overcharged import handle_overcharged
from dotenv import load_dotenv
import os

load_dotenv()

def get_refund_turnaround_time():
    return "5-7"

def clear_console():
    """
    Clears the terminal console dynamically based on the operating system.
    """
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

if __name__ == "__main__":
    
    while True:
        clear_console()
        print("Welcome to Food Panda Support!")
        print("Food Panda Support - Odrer ID: 12345")
        
        print("1. What is the refund turnaround time?")
        print("2. Check refund status")
        print("3. I have been overcharged")
        print("4. I didn't receive invoice")
        print("5. General Questions")
        print("6. General feedback")
        
        choice = input("Please enter your choice: ")
        
        if choice == "1":
            turnaround_time = get_refund_turnaround_time()
            print(f"The refund turnaround time is {turnaround_time} business days.")
        elif choice == "2":
            handle_refund()
        elif choice == "3":
            handle_overcharged()
        elif choice == "4":
            print("We have mailed you the invoice. Please check your email.")
        elif choice == "5":
            handle_general_query()
        elif choice == "6":
            feedback = input("Please enter your feedback: ")
            print("Thank you for your feedback! We will use it to improve our services.")
        else:
            print("Invalid choice. Please try again.")