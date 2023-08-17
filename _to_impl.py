import argparse
import sys

def main(extra_arg, required_arg1, required_arg2, optional_arg1, optional_arg2):
    print(f"Extra argument: {extra_arg}")
    print(f"Required argument 1: {required_arg1}")
    print(f"Required argument 2: {required_arg2}")
    print(f"Optional argument 1: {optional_arg1}")
    print(f"Optional argument 2: {optional_arg2}")

if __name__ == "__main__":
    script_name = sys.argv[0]

    parser = argparse.ArgumentParser(description="This script accepts multiple arguments, including two required arguments and two optional arguments with default values. Use the -h or --help flag for more information on the available arguments.")
    parser.add_argument("extra_arg", help="Extra positional argument", type=str)
    parser.add_argument("-r1", "--required1", help="Required argument 1", type=str)
    parser.add_argument("-r2", "--required2", help="Required argument 2", type=str)
    parser.add_argument("-o1", "--optional1", help="Optional argument 1 (default: 'default_value1')", type=str, default="default_value1")
    parser.add_argument("-o2", "--optional2", help="Optional argument 2 (default: 'default_value2')", type=str, default="default_value2")

    args = parser.parse_args()

    if len(sys.argv) == 2:
        required_input1 = input("Please enter the required argument 1: ")
        required_input2 = input("Please enter the required argument 2: ")
        optional_input1 = input(f"Please enter the optional argument 1 (leave blank for default '{args.optional1}'): ")
        optional_input2 = input(f"Please enter the optional argument 2 (leave blank for default '{args.optional2}'): ")
        main(args.extra_arg, required_input1, required_input2, optional_input1 if optional_input1 else args.optional1, optional_input2 if optional_input2 else args.optional2)
    else:
        if args.required1 is None or args.required2 is None:
            print("Error: the following arguments are required: -r1/--required1, -r2/--required2")
            sys.exit(1)
        main(args.extra_arg, args.required1, args.required2, args.optional1, args.optional2)