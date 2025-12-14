# Steam Depot Lua Generator

A Python-based tool with a graphical user interface to download the latest Steam depot keys, intelligently map them to application IDs (AppIDs), and generate corresponding `.lua` files.

## Features

- **GUI Interface**: Easy-to-use graphical interface built with Tkinter.
- **Fetches Latest Data**: Downloads the most recent depot keys and the official Steam AppID list directly from their sources.
- **Smart Depot Mapping**: An intelligent algorithm maps depots to their corresponding AppIDs. It can:
    - Find exact AppID-DepotID matches.
    - Search for AppIDs within a logical range of a depot ID.
    - Group unidentified depots that are numerically close, assuming they belong to the same unlisted application.
- **Lua File Generation**: Creates individual `.lua` files for each identified application, containing the AppID and its associated depots and keys.
- **Detailed Reporting**: Generates a `depot_mapping.json` file to show how depots were mapped, and a `statistics.json` file with a summary of the process.
- **Customization**: Allows users to specify an output directory and choose whether to skip generating files for unidentified applications.

## How It Works

1.  **Data Loading**: The tool first downloads two key JSON files:
    - [A list of Steam depot keys.](https://raw.githubusercontent.com/SteamAutoCracks/ManifestHub/refs/heads/main/depotkeys.json)
    - [A list of all Steam applications (AppIDs and names).](https://raw.githubusercontent.com/dgibbs64/SteamCMD-AppID-List/refs/heads/main/steamcmd_appid.json)
2.  **Smart Mapping**: The core of the script iterates through every valid depot. For each depot, it attempts to find the most likely parent AppID using a set of rules. Depots that cannot be matched to a known Steam game are grouped together based on proximity.
3.  **File Generation**: For each AppID and its list of associated depots, the script generates a `{appid}.lua` file in the specified output directory.
4.  **Reporting**: A summary `README.txt` is created in the output folder, along with JSON files for mapping and statistics, giving you a clear overview of the results.

## Usage

1.  Run the `steam_lua_generator.py` script or use Python.
    ```bash
    python steam_lua_generator.py
    ```
2.  The graphical user interface will appear.
3.  (Optional) Change the output directory from the default `lua_output`.
4.  (Optional) Check "Skip unknown apps" if you only want `.lua` files for recognized Steam games.
5.  Click the **"Start Generation"** button.
6.  The process will begin, and the progress bar and status labels will keep you updated.
7.  Once finished, you will find the generated `.lua` files and reports in the output directory.

## Output Files

In your designated output directory, you will find:

-   **`{appid}.lua`**: Lua script for each application.
-   **`depot_mapping.json`**: A detailed JSON file showing which depots were assigned to each AppID.
-   **`statistics.json`**: High-level statistics, such as the number of known vs. unknown apps found.
-   **`README.txt`**: A human-readable summary of the generation process, including the top 30 apps by depot count.

## Dependencies

-   Python 3.x
-   `requests`

You can install the required package using pip:
```bash
pip install requests
```

