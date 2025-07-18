import os
import sqlite3
from sentence_transformers import SentenceTransformer, util
from mcp.server.fastmcp import FastMCP
from typing import Any

# === Sabitler ===
DB_PATH = "file_records.db"
INDEX_FILE = "selma.index"
SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

file_description_dict = {
    "txt": "Text File", "docx": "Word Document", "doc": "Word Document (Old)",
    "pdf": "PDF Document", "xls": "Excel Spreadsheet", "xlsx": "Excel Workbook",
    "ppt": "PowerPoint Presentation", "pptx": "PowerPoint Presentation",
    "jpg": "Image File", "jpeg": "Image File", "png": "Image File", "svg": "Vector Image",
    "gif": "Animated Image", "bmp": "Bitmap Image", "csv": "CSV File", "tsv": "TSV File",
    "json": "JSON File", "xml": "XML File", "ini": "Configuration File", "log": "Log File",
    "py": "Python Script", "ipynb": "Jupyter Notebook", "html": "HTML File", "htm": "HTML File",
    "css": "CSS File", "js": "JavaScript File", "md": "Markdown File", "yml": "YAML File",
    "yaml": "YAML File", "exe": "Executable File", "msi": "Windows Installer",
    "apk": "Android App Package", "zip": "ZIP Archive", "rar": "RAR Archive",
    "7z": "7-Zip Archive", "tar": "Tar Archive", "gz": "GZip Archive", "iso": "Disk Image",
    "mp3": "Audio File", "wav": "Audio File", "ogg": "Audio File", "flac": "Lossless Audio",
    "mp4": "Video File", "avi": "Video File", "mkv": "Video File", "mov": "Apple Video File",
    "cpp": "C++ Source Code", "c": "C Source Code", "h": "Header File", "sh": "Shell Script",
    "bat": "Batch File", "dll": "Dynamic Link Library", "bin": "Binary Data File",
    "dat": "Data File", "bak": "Backup File", "kicad_pcb": "KiCad PCB File",
    "kicad_pro": "KiCad Project File", "kicad_sch": "KiCad Schematic",
    "r0d": "CST Simulation Result", "rpp": "CST Report File", "pipar": "CST Parameter File",
    "rps": "CST Plot Settings", "sweep": "CST Sweep File", "cwr": "CST Waveform Result",
    "rex": "CST Result Export File", "m3t": "Mesh File", "tet": "Tetrahedral Mesh",
    "stx": "Simulation Text File", "slv": "Solver Config", "svd": "Singular Value Data",
    "enc": "Encrypted File", "msg": "Message Resource File", "chk": "Checksum File",
    "tcl": "Tcl Script", "tm": "Tcl Module", "map": "Game Save File or Memory Map File",
    "webm": "WebM Video File", "webp": "WebP Image File", "pl": "Perl Script File",
    "lst": "List File (Plain Text)", "add": "Add-on Definition File",
    "rmv": "Removed Component File or Custom App Format", "ino": "Arduino Sketch File",
    "ads": "CST Project File", "alc": "CST Layout Component", "bwc": "CST Waveform Component",
    "dib": "Device Independent Bitmap", "dsn": "Design File", "ems": "Electromagnetic Structure",
    "fct": "Field Calculation Template", "gdc": "Geometry Definition Component",
    "hid": "Hidden Layer File", "jopt": "Job Optimization File", "pim": "Parameter Information",
    "cha": "Channel Assignment", "chksm": "Checksum File", "ci": "Circuit Information",
    "cpt": "Component File", "crd": "Card File", "dbp": "Database Pointer",
    "dpl": "Deployment Configuration", "dsi": "Design Setup Information",
    "et": "Tetrahedral Mesh", "exp": "Exported File", "fld": "Field Definition",
    "fgr": "Figure File", "fmd": "Field Model Definition", "grp": "Group File",
    "het": "Heterogeneous Config", "hp": "Harmonic Profile", "hsu": "Hybrid Setup",
    "ifo": "Input Format Object", "im": "Image Metadata", "imp": "Impedance File",
    "mch": "Mechanism Definition", "mif": "Material Information", "mot": "Motion File",
    "mst": "Mesh Structure", "mvm": "Movement File", "opg": "Output Plot Graph",
    "opticalcarriergeneration": "Optical Carrier Generation File", "pck2": "Package Data File",
    "pik2": "Pick Place File", "pin": "Pin Definition File", "plc": "PLC Configuration",
    "pmg": "Power Management Graph", "pms": "Power Management Script",
    "tec": "Technology File", "tem": "Template File", "tri": "Triangle Mesh",
    "trm": "Terminal Configuration", "trt": "Transient Result Template",
    "tsp": "Time Sampled Plot", "vde": "Voltage Definition Element",
    "vol": "Volume Definition", "vwr": "Viewer File", "wcs": "Waveform Configuration Set",
    "wir": "Wiring File", "xyz": "XYZ Coordinate File", "res": "Result File",
    "sat": "Saturation Data", "mdg": "Modeling Group File", "sconf": "Solver Configuration File",
    "sdb": "Simulation DB",
    "asc": "LTspice Circuit File",
    "raw": "LTspice Simulation Output",
    "log": "Simulation Log File",
}

FILTERED_EXTENSIONS = {".lnk", ".ini", ".tmp", ".sys", ".bak", ".log", ""}

# === MCP Server Setup ===
mcp = FastMCP("SmartFileMCP")

# === Yardımcı Fonksiyonlar ===
def get_file_description(extension):
    return file_description_dict.get(extension.lower().replace(".", ""), "Unknown File Type")

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS files")
    cursor.execute("""
        CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            directory TEXT,
            extension TEXT,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()
    

def list_files(folder_path):
    file_entries = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext.lower() in FILTERED_EXTENSIONS:
                continue
            desc = get_file_description(ext)
            file_entries.append((file, root, ext, desc))
    return file_entries

def save_to_index_and_db(file_entries):
    with open(INDEX_FILE, "w", encoding="utf-8") as f, sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for file_name, directory, ext, desc in file_entries:
            cursor.execute("INSERT INTO files (file_name, directory, extension, description) VALUES (?, ?, ?, ?)",
                           (file_name, directory, ext, desc))
            # Index dosyasına yaz
            file_path = os.path.join(directory, file_name).replace("\\", "/")
            uri_path = f"file:///{file_path}"
            f.write(f"{file_name} | {directory} | {ext} | {desc} | {uri_path}\n")


def read_index_file():
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

def semantic_search(question, content_lines, top_k=10):
    query_embedding = SBERT_MODEL.encode(question, convert_to_tensor=True)
    content_embeddings = SBERT_MODEL.encode(content_lines, convert_to_tensor=True)
    similarities = util.cos_sim(query_embedding, content_embeddings)[0]
    top_results = similarities.topk(k=min(top_k, len(content_lines)))
    return [content_lines[i] for i in top_results.indices]



@mcp.tool()
def index_folder(folder_path: str) -> str:
    """Index a folder and save files to database and index file."""
    if not os.path.isdir(folder_path):
        return "Invalid folder path."
    initialize_database()
    files = list_files(folder_path)
    save_to_index_and_db(files)
    return f"{len(files)} files indexed successfully."

@mcp.tool()
def search_files(question: str, top_k: int = 15) -> list[dict]:
    """Perform semantic search on indexed files."""
    content_lines = read_index_file()
    if not content_lines:
        return [{"error": "No index file found."}]
    
    matches = semantic_search(question, content_lines, top_k=top_k)
    results = []
    for line in matches:
        parts = line.split("|")
        if len(parts) >= 5:
            results.append({
                "file_name": parts[0].strip(),
                "directory": parts[1].strip(),
                "extension": parts[2].strip(),
                "description": parts[3].strip(),
                "uri": parts[4].strip()
            })
    return results if results else [{"message": "No relevant results found."}]

@mcp.resource("file://{file_id}")
def get_file_info(file_id: str) -> dict:
    """Get information about a specific file by its ID (simulated as file_name for now)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE file_name = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "file_name": row[1],
            "directory": row[2],
            "extension": row[3],
            "description": row[4]
        }
    return {"error": "File not found."}

@mcp.prompt()
def file_search_prompt(query: str) -> str:
    """Generate a prompt for file searching."""
    return f"Search for files related to: {query}. Provide details on matches including names, descriptions, and URIs."

if __name__ == "__main__":
    # Sunucuyu çalıştır (örneğin stdio için geliştirme, veya streamable-http için üretim)
    mcp.run(transport="stdio")