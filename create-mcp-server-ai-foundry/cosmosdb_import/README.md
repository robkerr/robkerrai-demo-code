# Movie Data Import for Cosmos DB Gremlin

This script imports movie data from CSV format into Azure Cosmos DB using the Gremlin (Graph) API.

## Graph Schema

### Vertices
- **Movie**: id, title, year, duration, description, avg_vote, votes
- **Person**: id, name (actors, directors, writers)
- **Genre**: id, name
- **ProductionCompany**: id, name

### Edges
- **Person -[DIRECTED]-> Movie**
- **Person -[ACTED_IN]-> Movie**
- **Person -[WROTE]-> Movie**
- **Movie -[HAS_GENRE]-> Genre**
- **Movie -[PRODUCED_BY]-> ProductionCompany**

## Prerequisites

1. **Azure Cosmos DB Account** with Gremlin API enabled
2. **Database and Collection** created in Cosmos DB
3. **Python 3.8+** installed

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Cosmos DB credentials
```

3. Get your Cosmos DB credentials from Azure Portal:
   - Navigate to your Cosmos DB account
   - Go to "Keys" section
   - Copy the Gremlin Endpoint (format: `wss://your-account.gremlin.cosmos.azure.com:443/`)
   - Copy the Primary Key or Secondary Key

## Usage

### Import CSV data (append to existing):
```bash
python import_movies.py path/to/movies.csv
```

### Clear existing data and import fresh:
```bash
python import_movies.py path/to/movies.csv --clear
```

## CSV Format

The script expects a CSV file with the following columns:

- `imdb_title_id`: Unique movie identifier
- `original_title`: Movie title
- `year`: Release year
- `genre`: Comma-separated genres (e.g., "Action, Drama")
- `duration`: Duration in minutes
- `director`: Director name
- `writer`: Comma-separated writer names
- `production_company`: Production company name
- `actors`: Comma-separated actor names
- `description`: Movie description
- `avg_vote`: Average rating
- `votes`: Number of votes

## Example CSV Row

```csv
imdb_title_id,original_title,year,genre,duration,director,writer,production_company,actors,description,avg_vote,votes
tt0111161,The Shawshank Redemption,1994,Drama,142,Frank Darabont,"Stephen King, Frank Darabont",Castle Rock Entertainment,"Tim Robbins, Morgan Freeman, Bob Gunton",Two imprisoned men bond...,9.3,2278845
```

## Troubleshooting

### Connection Issues
- Ensure your Cosmos DB firewall allows connections from your IP
- Verify the endpoint URL includes the `wss://` protocol and `:443` port

### Performance
- The script processes movies sequentially to avoid overwhelming the Cosmos DB
- For large datasets (>1000 movies), consider batch operations or Azure Data Factory

### Rate Limiting
- Cosmos DB has Request Unit (RU) limits
- If you encounter 429 errors, the script will need retry logic added
- Consider increasing your collection's RU/s temporarily during import

## Notes

- Person vertices are deduplicated (same person appearing as actor/director/writer)
- Genre and ProductionCompany vertices are also deduplicated
- The `--clear` flag will delete ALL data in the graph before importing
- Import progress is displayed every 10 movies
