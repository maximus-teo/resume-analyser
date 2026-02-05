import json

def sort_json(input_filename, output_filename):
    """
    Use sort.py to sort a JSON file alphabetically
    """
    try:
        with open(input_filename, 'r') as file:
            data = json.load(file)
            sorted_data_str = json.dumps(data, sort_keys=True, indent=4)
            sorted_data = json.loads(sorted_data_str)

        with open(output_filename, 'w') as file:
            json.dump(sorted_data, file, indent=4) # pretty printing
            print(f"Successfully sorted '{input_filename}' and saved to '{output_filename}'.")

    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_filename}'.")
    except Exception as e:
        print(f"Some error occurred: {e}")

# INSERT YOUR FILE NAMES HERE
sort_json('app/assets/skills_operations_hard.json', 'app/assets/skills_operations_hard_sorted.json')