import json

def convert_txt_to_json(input_filename, output_filename):
    """
    Use parse.py to quickly convert a text file of single values into a JSON file containing a list of values (not key-value pairs)
    """
    data = []

    try:
        with open(input_filename, 'r') as txt_file:
            for line in txt_file:
                line = line.strip()
                if line:
                    try: data.append(line)
                    except ValueError: print(f"Warning: skipping malformed line in '{input_filename}': '{line}'")

        with open(output_filename, 'w') as json_file:
            json.dump(data, json_file, sort_keys=True, indent=4) # pretty printing
            print(f"Successfully parsed '{input_filename}' to '{output_filename}'.")

    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.")
    except Exception as e:
        print(f"Some error occurred: {e}")

# INSERT YOUR FILE NAMES HERE
convert_txt_to_json('app/assets/data.txt', 'app/assets/skills_operations_hard2.json')