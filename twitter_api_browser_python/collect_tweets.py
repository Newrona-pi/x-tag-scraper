import asyncio
import csv
import json
from datetime import datetime
from typing import List, Dict, Any

from main import TwitterAPIBrowser

async def collect_tweets(
    hashtag: str,
    start_date: str,
    end_date: str,
    output_file: str,
    limit: int = 100
) -> None:
    """
    Collects tweets with a specific hashtag within a date range and saves them to CSV.
    
    Args:
        hashtag: The hashtag to search for (e.g., "#example").
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        output_file: Path to the output CSV file.
        limit: Maximum number of tweets to collect (approximate).
    """
    user_data_dir = "./.data"
    
    # Construct the search query
    # Example: #hashtag since:2023-01-01 until:2023-01-31
    query = f"{hashtag} since:{start_date} until:{end_date}"
    print(f"Searching for: {query}")

    async with TwitterAPIBrowser(user_data_dir=user_data_dir) as browser:
        await browser.login()
        inject = await browser.inject()
        
        collected_tweets = []
        cursor = None
        
        while len(collected_tweets) < limit:
            print(f"Collecting... (Current count: {len(collected_tweets)})")
            
            variables = {
                "rawQuery": query,
                "count": 50,
                "querySource": "typed_query",
                "product": "Latest",
                "withGrokTranslatedBio": False,
            }
            
            if cursor:
                variables["cursor"] = cursor

            try:
                res = await inject.request(
                    "SearchTimeline",
                    variables
                )
            except Exception as e:
                print(f"Error during request: {e}")
                break

            # Parse the response
            try:
                timeline = res["data"]["search_by_raw_query"]["search_timeline"]["timeline"]
                instructions = timeline["instructions"]
                
                entries = []
                for instruction in instructions:
                    if instruction["type"] == "TimelineAddEntries":
                        entries = instruction["entries"]
                        break
                    elif instruction["type"] == "TimelineReplaceEntry":
                        # Sometimes used for cursor updates or single entry updates
                        if instruction["entry"]["entryIdToReplace"] == "cursor-bottom-0":
                             entries.append(instruction["entry"])

                
                new_tweets_found = False
                bottom_cursor = None

                for entry in entries:
                    try:
                        content = entry["content"]
                        
                        # Handle Cursor
                        if content["entryType"] == "TimelineTimelineCursor":
                            # Accept both Bottom and ShowMore cursors to continue pagination
                            if content["cursorType"] == "Bottom" or content["cursorType"] == "ShowMore":
                                bottom_cursor = content["value"]
                            continue

                        # Handle Tweet
                        if content["entryType"] == "TimelineTimelineItem":
                            item_result = content["itemContent"]["tweet_results"].get("result")
                            
                            # Handle retweets or missing data
                            if not item_result:
                                continue
                                
                            if "tweet" in item_result: # Handle nested tweet object (e.g. in some search results)
                                item_result = item_result["tweet"]
                                
                            if "legacy" not in item_result:
                                continue

                            legacy = item_result["legacy"]
                            
                            # Check for user data
                            if "core" not in item_result or "user_results" not in item_result["core"]:
                                continue
                                
                            user_result = item_result["core"]["user_results"]["result"]
                            
                            # Handle case where user data is wrapped in 'user' key or directly in legacy
                            if "legacy" in user_result:
                                user_legacy = user_result["legacy"]
                            elif "user" in user_result and "legacy" in user_result["user"]: # Sometimes nested differently
                                user_legacy = user_result["user"]["legacy"]
                            else:
                                # Fallback or skip
                                print(f"DEBUG: No legacy found in user_result keys: {user_result.keys()}")
                                continue
                            
                            # Extract Data
                            tweet_id = legacy["id_str"]
                            
                            # Try to find name/screen_name in legacy
                            screen_name = user_legacy.get("screen_name")
                            author_name = user_legacy.get("name")
                            
                            # Fallback: Check if they are in 'core' (based on user finding)
                            if not screen_name and "core" in user_result:
                                 screen_name = user_result["core"].get("screen_name")
                            if not author_name and "core" in user_result:
                                 author_name = user_result["core"].get("name")

                            # Fallback: Check top level of user_result
                            if not screen_name and "screen_name" in user_result:
                                 screen_name = user_result["screen_name"]
                            if not author_name and "name" in user_result:
                                 author_name = user_result["name"]
                                 
                            # If still unknown
                            if not screen_name: screen_name = "Unknown"
                            if not author_name: author_name = "Unknown"

                            # Basic Info
                            post_date = legacy["created_at"] # Format: Wed Oct 10 20:19:24 +0000 2018
                            
                            # Convert Date format
                            try:
                                dt = datetime.strptime(post_date, "%a %b %d %H:%M:%S %z %Y")
                                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                formatted_date = post_date

                            post_link = f"https://x.com/{screen_name}/status/{tweet_id}"
                            
                            # Metrics
                            repost_count = legacy.get("retweet_count", 0)
                            favorite_count = legacy.get("favorite_count", 0)
                            
                            # Views/Impressions (Sometimes in 'views' object, sometimes not available)
                            impression_count = 0
                            if "views" in item_result and "count" in item_result["views"]:
                                 impression_count = int(item_result["views"]["count"])

                            # Hashtags
                            hashtags = [tag["text"] for tag in legacy.get("entities", {}).get("hashtags", [])]
                            # Filter out the search tag (case insensitive)
                            search_tag_clean = hashtag.replace("#", "").lower()
                            other_tags = [f"#{tag}" for tag in hashtags if tag.lower() != search_tag_clean]
                            
                            tweet_data = {
                                "Author Name": author_name,
                                "Post Date": formatted_date,
                                "Post Link": post_link,
                                "Other Hashtags": ", ".join(other_tags),
                                "Repost Count": repost_count,
                                "Impression Count": impression_count,
                                "Like Count": favorite_count
                            }
                            
                            collected_tweets.append(tweet_data)
                            new_tweets_found = True
                    except Exception as e:
                        # print(f"Skipping a tweet due to error: {e}")
                        continue

                # if not new_tweets_found:
                #     print("No new tweets found in this batch.")
                #     # Don't break here immediately, sometimes there are gaps or only cursors
                #     # break
                
                # Extract cursor from instructions if available (often more reliable than finding it in entries)
                for instruction in instructions:
                    if instruction["type"] == "TimelineAddEntries":
                        for entry in instruction["entries"]:
                            if entry["content"]["entryType"] == "TimelineTimelineCursor" and entry["content"]["cursorType"] == "Bottom":
                                bottom_cursor = entry["content"]["value"]
                    elif instruction["type"] == "TimelineReplaceEntry":
                         if instruction["entry"]["content"]["entryType"] == "TimelineTimelineCursor" and instruction["entry"]["content"]["cursorType"] == "Bottom":
                                bottom_cursor = instruction["entry"]["content"]["value"]

                # If we didn't find it in instructions, check the entries loop we just did (which might have found it)
                # But actually, let's rely on the instruction scan above as primary.
                
                if not bottom_cursor:
                     # Fallback: sometimes it's just in the entries list we iterated
                     for entry in entries:
                        if entry["content"]["entryType"] == "TimelineTimelineCursor" and entry["content"]["cursorType"] == "Bottom":
                            bottom_cursor = entry["content"]["value"]

                if not bottom_cursor or bottom_cursor == cursor:
                    print(f"Reached end of timeline. Cursor: {bottom_cursor}")
                    break
                
                cursor = bottom_cursor
                await asyncio.sleep(2) # Be polite

            except KeyError as e:
                print(f"Error parsing response: {e}")
                # print(json.dumps(res, indent=2)) # Debug
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break

    # Write to CSV
    if collected_tweets:
        print(f"Writing {len(collected_tweets)} tweets to {output_file}")
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=collected_tweets[0].keys())
            writer.writeheader()
            writer.writerows(collected_tweets)
    else:
        print("No tweets collected.")

if __name__ == "__main__":
    # Example Usage
    # You can change these values
    TARGET_HASHTAG = "#Python"
    START_DATE = "2023-01-01"
    END_DATE = "2023-12-31"
    OUTPUT_FILE = "tweets.csv"
    
    # Prompt user for input if running directly
    import sys
    if len(sys.argv) > 1:
        # If arguments provided, could parse them, but for now let's stick to interactive or hardcoded for the example
        pass
    else:
        print("--- Tweet Collector ---")
        TARGET_HASHTAG = input("Enter hashtag (e.g. #Python): ") or TARGET_HASHTAG
        START_DATE = input("Enter start date (YYYY-MM-DD): ") or START_DATE
        END_DATE = input("Enter end date (YYYY-MM-DD): ") or END_DATE
    
    asyncio.run(collect_tweets(TARGET_HASHTAG, START_DATE, END_DATE, OUTPUT_FILE))
