"""
MedFront Action Layer - Standalone Interactive CLI Runner.
Allows isolated manual testing, verification, and interactive simulation
of Module 5 healthcare action tools without requiring live phone calls or OpenAI.
"""

import json
import sys
from datetime import date, timedelta
from src.actions.schemas import HEALTHCARE_TOOLS
from src.actions.tools import execute_tool, get_db_service


def print_header():
    print("\n" + "=" * 65)
    print(" [MedFront Voice AI] - Module 5: Action Layer CLI Runner")
    print("=" * 65)


def run_simulation():
    print("\n--- [SIMULATION] Running End-to-End Simulation Flow ---")
    
    # 1. Verification
    print("\n1. Verifying Patient 'Robert Chen' (DOB: 1985-04-12)...")
    res1 = execute_tool("verify_patient_identity", {
        "first_name": "Robert",
        "last_name": "Chen",
        "date_of_birth": "1985-04-12"
    })
    print(f"Result: {json.dumps(res1, indent=2)}")
    patient_id = res1["data"]["patient_id"]

    # 2. Check Availability
    target_date = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    print(f"\n2. Checking Availability for 'Dr. Sarah Smith (Cardiology)' on {target_date}...")
    res2 = execute_tool("check_schedule_availability", {
        "doctor_name_or_specialty": "Dr. Sarah Smith",
        "target_date": target_date
    })
    print(f"Result: {json.dumps(res2, indent=2)}")
    available_slot = res2["data"]["schedules"][0]["available_slots"][0]

    # 3. Book Slot
    print(f"\n3. Booking slot '{available_slot}' for Patient {patient_id}...")
    res3 = execute_tool("book_appointment", {
        "patient_id": patient_id,
        "doctor_name": "Dr. Sarah Smith",
        "appointment_date": target_date,
        "appointment_time": available_slot,
        "reason_for_visit": "Chest tightness and follow-up consultation"
    })
    print(f"Result: {json.dumps(res3, indent=2)}")
    appt_id = res3["data"]["id"]

    # 4. Prevent Double-Booking
    print(f"\n4. Testing Race Condition: Attempting duplicate booking on same slot '{available_slot}'...")
    res4 = execute_tool("book_appointment", {
        "patient_id": "P-10024",
        "doctor_name": "Dr. Sarah Smith",
        "appointment_date": target_date,
        "appointment_time": available_slot,
        "reason_for_visit": "Another patient booking same slot"
    })
    print(f"Result: {json.dumps(res4, indent=2)}")
    assert not res4["success"], "Expected double booking to be rejected!"

    # 5. List Appointments
    print(f"\n5. Retrieving booked appointments for Patient {patient_id}...")
    res5 = execute_tool("get_patient_appointments", {
        "patient_id": patient_id
    })
    print(f"Result: {json.dumps(res5, indent=2)}")

    # 6. Cancel Appointment
    print(f"\n6. Cancelling Appointment {appt_id}...")
    res6 = execute_tool("cancel_appointment", {
        "patient_id": patient_id,
        "appointment_id": appt_id
    })
    print(f"Result: {json.dumps(res6, indent=2)}")

    print("\n[OK] Simulation completed successfully with all assertions met!\n")


def interactive_menu():
    print_header()
    today_str = date.today().strftime("%Y-%m-%d")

    while True:
        print("\nSelect an action:")
        print("1. Verify Patient Identity")
        print("2. Check Doctor Schedule Availability")
        print("3. Book an Appointment")
        print("4. View Patient Booked Appointments")
        print("5. Cancel an Appointment")
        print("6. Run Automated End-to-End Simulation")
        print("7. Inspect OpenAI Tool Schemas (JSON)")
        print("8. Exit")

        choice = input("\nEnter choice [1-8]: ").strip()

        if choice == "1":
            fn = input("First Name (e.g. Robert): ").strip()
            ln = input("Last Name (e.g. Chen): ").strip()
            dob = input("Date of Birth [YYYY-MM-DD] (e.g. 1985-04-12): ").strip()
            res = execute_tool("verify_patient_identity", {
                "first_name": fn, "last_name": ln, "date_of_birth": dob
            })
            print(f"\n{json.dumps(res, indent=2)}")

        elif choice == "2":
            doc = input("Doctor name or specialty (e.g. Dr. Sarah Smith / Cardiology): ").strip()
            dt = input(f"Target Date [YYYY-MM-DD] (default: {today_str}): ").strip() or today_str
            res = execute_tool("check_schedule_availability", {
                "doctor_name_or_specialty": doc, "target_date": dt
            })
            print(f"\n{json.dumps(res, indent=2)}")

        elif choice == "3":
            pid = input("Patient ID (e.g. P-10023): ").strip()
            doc = input("Doctor Name (e.g. Dr. Sarah Smith): ").strip()
            dt = input(f"Appointment Date [YYYY-MM-DD] (default: {today_str}): ").strip() or today_str
            tm = input("Appointment Time (e.g. 10:00 AM): ").strip()
            reason = input("Reason for visit: ").strip() or "General Consultation"
            res = execute_tool("book_appointment", {
                "patient_id": pid,
                "doctor_name": doc,
                "appointment_date": dt,
                "appointment_time": tm,
                "reason_for_visit": reason
            })
            print(f"\n{json.dumps(res, indent=2)}")

        elif choice == "4":
            pid = input("Patient ID (e.g. P-10023): ").strip()
            res = execute_tool("get_patient_appointments", {"patient_id": pid})
            print(f"\n{json.dumps(res, indent=2)}")

        elif choice == "5":
            pid = input("Patient ID (e.g. P-10023): ").strip()
            aid = input("Appointment ID (e.g. APT-XXXXXX): ").strip()
            res = execute_tool("cancel_appointment", {
                "patient_id": pid, "appointment_id": aid
            })
            print(f"\n{json.dumps(res, indent=2)}")

        elif choice == "6":
            run_simulation()

        elif choice == "7":
            print("\nRegistered OpenAI Tool Schemas:")
            print(json.dumps(HEALTHCARE_TOOLS, indent=2))

        elif choice == "8":
            print("\nExiting CLI. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Please enter 1-8.")


if __name__ == "__main__":
    interactive_menu()
