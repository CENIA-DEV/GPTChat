import datetime
import glob
import json
from typing import Dict, Optional, List
import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

types = {
    "share",
    "chat",
    "flag",
    "bothbad_vote",
    "downvote",
    "leftvote",
    "rightvote",
    "upvote",
    "tievote",
}

def process_record(record: Dict, username: Optional[str] = None) -> Optional[Dict]:
    """
    Process a single record and return it if it meets the criteria.
    
    Args:
        record: The record to process
        username: Optional username to filter by
    """
    mtype = record.get("type")
    if not mtype:
        logger.warning(f"Record missing type field: {record}")
        return None
        
    if mtype not in types:
        logger.warning(f"Unknown record type: {mtype}")
        return None

    # Username filtering if specified
    if username:
        record_username = record.get("username")
        if not record_username or record_username != username:
            return None

    # We want to keep all vote-related records
    if mtype in ("leftvote", "rightvote", "bothbad_vote", "tievote", "upvote", "downvote"):
        return record
        
    return None

def process_file(infile: str, outfile: str, username: Optional[str] = None) -> None:
    """
    Process a single file and append filtered records to the output file.
    
    Args:
        infile: Input file path
        outfile: Output file path
        username: Optional username to filter by
    """
    logger.info(f"Processing file: {infile}")
    records_count = 0
    filtered_count = 0
    
    try:
        with open(infile) as f:
            records: List[Dict] = []
            for line_num, l in enumerate(f.readlines(), 1):
                l = l.strip()
                if not l:
                    continue
                    
                try:
                    r = json.loads(l)
                    if r.get("tstamp") is not None:
                        records.append(r)
                        records_count += 1
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON at line {line_num} in {infile}")
                except Exception as e:
                    logger.error(f"Error processing line {line_num} in {infile}: {str(e)}")

            # sort the records in case there are out-of-order records
            records.sort(key=lambda x: x["tstamp"])
            
            with open(outfile, "a") as out_f:
                for r in records:
                    try:
                        output = process_record(r, username)
                        if output is not None:
                            out_f.write(json.dumps(output) + "\n")
                            filtered_count += 1
                    except Exception as e:
                        logger.error(f"Error processing record: {str(e)}")
                        
    except Exception as e:
        logger.error(f"Error processing file {infile}: {str(e)}")
        
    logger.info(f"File {infile}: processed {records_count} records, kept {filtered_count} records")

def data_filter(path: str, output_file: str, username: Optional[str] = None) -> None:
    """
    Filter data files matching the given path pattern.
    
    Args:
        path: Path pattern to match files
        output_file: Output file path
        username: Optional username to filter by
    """
    logger.info(f"Starting data filtering with pattern: {path}")
    logger.info(f"Output file: {output_file}")
    if username:
        logger.info(f"Filtering for username: {username}")
    
    # Clear the output file before starting
    open(output_file, 'w').close()
    
    today = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filelist = sorted(glob.glob(path))
    
    # Filter out today's files and non-json files
    filelist = [
        f for f in filelist 
        if today not in f and f.endswith('.json')
    ]
    
    if not filelist:
        logger.warning(f"No files found matching pattern: {path}")
        return
        
    logger.info(f"Found {len(filelist)} files to process")
    
    for f in tqdm.tqdm(filelist):
        process_file(f, output_file, username)
        
    logger.info("Data filtering completed")

def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Filter and process chat data files.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'path',
        type=str,
        help='Path pattern to input files (e.g., "data/*.json")'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='filtered_data.jsonl',
        help='Output file path'
    )
    parser.add_argument(
        '--username',
        type=str,
        help='Filter records by username'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        
    data_filter(args.path, args.output, args.username)

if __name__ == '__main__':
    main()
