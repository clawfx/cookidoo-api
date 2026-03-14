#!/usr/bin/env python3
"""Cookidoo CLI - Interact with Cookidoo recipe platform."""

import asyncio
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import aiohttp
from cookidoo_api import Cookidoo
from cookidoo_api.helpers import get_localization_options
from cookidoo_api.types import CookidooConfig
from dotenv import load_dotenv


def load_credentials():
    """Load credentials from credentials.env file."""
    # Look for credentials.env in the workspace root
    workspace_root = Path(__file__).resolve().parents[2]
    credentials_file = workspace_root / "credentials.env"
    
    if not credentials_file.exists():
        print(f"Error: credentials.env not found at {credentials_file}", file=sys.stderr)
        sys.exit(1)
    
    load_dotenv(credentials_file)
    
    email = os.getenv("COOKIDOO_EMAIL")
    password = os.getenv("COOKIDOO_PASSWORD")
    country = os.getenv("COOKIDOO_COUNTRY", "de-AT")
    
    if not email or not password:
        print("Error: COOKIDOO_EMAIL and COOKIDOO_PASSWORD must be set in credentials.env", file=sys.stderr)
        print("\nPlease add your Cookidoo credentials to credentials.env:", file=sys.stderr)
        print("  COOKIDOO_EMAIL=your@email.com", file=sys.stderr)
        print("  COOKIDOO_PASSWORD=yourpassword", file=sys.stderr)
        print(f"  COOKIDOO_COUNTRY={country}", file=sys.stderr)
        sys.exit(1)
    
    return email, password, country


def parse_country_code(country_str: str) -> tuple[str, str]:
    """Parse country code like 'de-AT' into country and language."""
    if "-" in country_str:
        lang, country = country_str.split("-", 1)
        return country.lower(), f"{lang}-{country}"
    return country_str.lower(), "en"


async def create_cookidoo_client() -> Cookidoo:
    """Create and authenticate Cookidoo client."""
    email, password, country = load_credentials()
    country_code, language = parse_country_code(country)
    
    session = aiohttp.ClientSession()
    
    try:
        localizations = await get_localization_options(
            country=country_code, 
            language=language
        )
        if not localizations:
            print(f"Error: No localization found for {country}", file=sys.stderr)
            await session.close()
            sys.exit(1)
        
        cookidoo = Cookidoo(
            session,
            cfg=CookidooConfig(
                email=email,
                password=password,
                localization=localizations[0],
            ),
        )
        
        await cookidoo.login()
        return cookidoo
    except Exception as e:
        await session.close()
        raise e


def output_json(data):
    """Output data as JSON."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def output_human(data, format_type="list"):
    """Output data in human-readable format."""
    if format_type == "shopping-list":
        print("\n🛒 Shopping List\n")
        
        if "ingredients" in data:
            if data["ingredients"]:
                print("📝 Recipe Ingredients:")
                for item in data["ingredients"]:
                    check = "✅" if item.get("checked") else "⬜"
                    qty = f" ({item['quantity']})" if item.get("quantity") else ""
                    print(f"  {check} {item['name']}{qty}")
                print()
            
        if "additional" in data:
            if data["additional"]:
                print("➕ Additional Items:")
                for item in data["additional"]:
                    check = "✅" if item.get("checked") else "⬜"
                    print(f"  {check} {item['name']}")
                print()
        
        if not data.get("ingredients") and not data.get("additional"):
            print("  (empty)\n")
    
    elif format_type == "recipes":
        print("\n📚 Saved Recipes\n")
        if data:
            for recipe in data:
                print(f"  • {recipe['name']}")
                if recipe.get('id'):
                    print(f"    ID: {recipe['id']}")
                print()
        else:
            print("  (none)\n")
    
    elif format_type == "meal-plan":
        print(f"\n📅 Meal Plan - Week {data.get('week', '?')}\n")
        if data.get("days"):
            for day in data["days"]:
                day_name = day.get("date", "?")
                recipes = day.get("recipes", [])
                print(f"  {day_name}:")
                if recipes:
                    for recipe in recipes:
                        print(f"    • {recipe['name']}")
                else:
                    print(f"    (no recipes)")
                print()
        else:
            print("  (no meal plan)\n")
    
    elif format_type == "success":
        print(f"✅ {data.get('message', 'Success')}")
    
    else:
        # Default list format
        if isinstance(data, list):
            for item in data:
                print(f"  • {item}")
        else:
            print(data)


async def cmd_shopping_list(args, human=False):
    """List all shopping list items."""
    cookidoo = await create_cookidoo_client()
    
    try:
        ingredients = await cookidoo.get_ingredient_items()
        additional = await cookidoo.get_additional_items()
        
        result = {
            "ingredients": [
                {
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.description,
                    "checked": item.is_owned,
                }
                for item in ingredients
            ],
            "additional": [
                {
                    "id": item.id,
                    "name": item.name,
                    "checked": item.is_owned,
                }
                for item in additional
            ],
        }
        
        if human:
            output_human(result, "shopping-list")
        else:
            output_json(result)
    
    finally:
        await cookidoo._session.close()


async def cmd_shopping_list_add(item_name: str, args, human=False):
    """Add an item to additional purchases."""
    cookidoo = await create_cookidoo_client()
    
    try:
        await cookidoo.add_additional_items([item_name])
        
        result = {"message": f"Added '{item_name}' to shopping list", "item": item_name}
        
        if human:
            output_human(result, "success")
        else:
            output_json(result)
    
    finally:
        await cookidoo._session.close()


async def cmd_shopping_list_check(item_name: str, args, human=False):
    """Check off an item from the shopping list."""
    cookidoo = await create_cookidoo_client()
    
    try:
        # Get all items
        ingredients = await cookidoo.get_ingredient_items()
        additional = await cookidoo.get_additional_items()
        
        # Find matching item
        matched_ingredient = None
        matched_additional = None
        
        for item in ingredients:
            if item_name.lower() in item.name.lower():
                matched_ingredient = item
                break
        
        for item in additional:
            if item_name.lower() in item.name.lower():
                matched_additional = item
                break
        
        if matched_ingredient:
            # Toggle the ownership status
            matched_ingredient.is_owned = not matched_ingredient.is_owned
            await cookidoo.edit_ingredient_items_ownership([matched_ingredient])
            status = "checked" if matched_ingredient.is_owned else "unchecked"
            result = {"message": f"{status.capitalize()} '{matched_ingredient.name}'", "item": matched_ingredient.name}
        elif matched_additional:
            # Toggle the ownership status
            matched_additional.is_owned = not matched_additional.is_owned
            await cookidoo.edit_additional_items_ownership([matched_additional])
            status = "checked" if matched_additional.is_owned else "unchecked"
            result = {"message": f"{status.capitalize()} '{matched_additional.name}'", "item": matched_additional.name}
        else:
            result = {"error": f"Item '{item_name}' not found in shopping list"}
            if human:
                print(f"❌ {result['error']}")
            else:
                output_json(result)
            sys.exit(1)
        
        if human:
            output_human(result, "success")
        else:
            output_json(result)
    
    finally:
        await cookidoo._session.close()


async def cmd_shopping_list_clear(args, human=False):
    """Clear the shopping list."""
    cookidoo = await create_cookidoo_client()
    
    try:
        await cookidoo.clear_shopping_list()
        
        result = {"message": "Shopping list cleared"}
        
        if human:
            output_human(result, "success")
        else:
            output_json(result)
    
    finally:
        await cookidoo._session.close()


async def cmd_recipes_saved(args, human=False):
    """List saved/bookmarked recipes."""
    cookidoo = await create_cookidoo_client()
    
    try:
        # Get both managed and custom collections
        managed = await cookidoo.get_managed_collections()
        custom = await cookidoo.get_custom_collections()
        
        result = []
        
        # Add managed collections
        for collection in managed:
            result.append({
                "id": collection.id,
                "name": collection.name,
                "type": "managed",
                "recipe_count": len(collection.recipe_ids) if hasattr(collection, 'recipe_ids') else 0,
            })
        
        # Add custom collections
        for collection in custom:
            result.append({
                "id": collection.id,
                "name": collection.name,
                "type": "custom",
                "recipe_count": len(collection.recipe_ids) if hasattr(collection, 'recipe_ids') else 0,
            })
        
        if human:
            output_human(result, "recipes")
        else:
            output_json(result)
    
    finally:
        await cookidoo._session.close()


async def cmd_recipes_search(query: str, args, human=False):
    """Search recipes (searches through saved collections)."""
    cookidoo = await create_cookidoo_client()
    
    try:
        # Note: The API doesn't provide a direct search function
        # We search through saved collections instead
        managed = await cookidoo.get_managed_collections()
        custom = await cookidoo.get_custom_collections()
        
        results = []
        query_lower = query.lower()
        
        # Search in collection names
        for collection in managed + custom:
            if query_lower in collection.name.lower():
                results.append({
                    "id": collection.id,
                    "name": collection.name,
                    "type": "collection",
                    "match": "name",
                })
        
        result = {
            "query": query,
            "results": results,
            "note": "Searching in saved collections only. Full recipe search not available via API."
        }
        
        if human:
            print(f"\n🔍 Search results for '{query}':\n")
            if results:
                for item in results:
                    print(f"  • {item['name']} (Collection)")
                    print(f"    ID: {item['id']}\n")
            else:
                print("  No results found.\n")
            print("Note: Searching in saved collections only.")
        else:
            output_json(result)
    
    finally:
        await cookidoo._session.close()


async def cmd_meal_plan(week_offset: int = 0, args=None, human=False):
    """Show meal plan for current or specified week."""
    cookidoo = await create_cookidoo_client()
    
    try:
        # Calculate the target date
        target_date = date.today() + timedelta(weeks=week_offset)
        
        # Get recipes for that week
        calendar_data = await cookidoo.get_recipes_in_calendar_week(target_date)
        
        # Calculate week number
        week_num = target_date.isocalendar()[1]
        
        result = {
            "week": week_num,
            "year": target_date.year,
            "days": []
        }
        
        for day in calendar_data:
            day_recipes = []
            
            # Add regular recipes
            for recipe in day.recipes:
                day_recipes.append({
                    "id": recipe.id,
                    "name": recipe.name,
                    "type": "regular"
                })
            
            # Add custom recipes (if attribute exists)
            if hasattr(day, 'custom_recipes'):
                for recipe in day.custom_recipes:
                    day_recipes.append({
                        "id": recipe.id,
                        "name": recipe.name,
                        "type": "custom"
                    })
            
            # day.id is date string like "2026-03-05", day.title is formatted date
            day_date = day.id if hasattr(day, 'id') else str(day.date) if hasattr(day, 'date') else "unknown"
            day_title = day.title if hasattr(day, 'title') else day_date
            
            result["days"].append({
                "date": day_date,
                "day_name": day_title,
                "recipes": day_recipes
            })
        
        if human:
            output_human(result, "meal-plan")
        else:
            output_json(result)
    
    finally:
        await cookidoo._session.close()


async def cmd_meal_plan_add(recipe_id: str, date_str: str, args, human=False):
    """Add a recipe to the meal plan."""
    cookidoo = await create_cookidoo_client()
    
    try:
        # Parse date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            result = {"error": f"Invalid date format: {date_str}. Use YYYY-MM-DD"}
            if human:
                print(f"❌ {result['error']}")
            else:
                output_json(result)
            sys.exit(1)
        
        # Add recipe to calendar (try regular first, then custom)
        try:
            await cookidoo.add_recipes_to_calendar(target_date, [recipe_id])
        except Exception:
            # Might be a custom recipe
            await cookidoo.add_custom_recipes_to_calendar(target_date, [recipe_id])
        
        result = {
            "message": f"Added recipe {recipe_id} to {date_str}",
            "recipe_id": recipe_id,
            "date": date_str
        }
        
        if human:
            output_human(result, "success")
        else:
            output_json(result)
    
    finally:
        await cookidoo._session.close()


def print_usage():
    """Print usage information."""
    print("""
Cookidoo CLI - Interact with Cookidoo recipe platform

Usage:
  cookidoo shopping-list [--human]
    List all items on the shopping list
  
  cookidoo shopping-list add <item> [--human]
    Add an item to additional purchases
  
  cookidoo shopping-list check <item> [--human]
    Toggle check status of an item
  
  cookidoo shopping-list clear [--human]
    Clear the entire shopping list
  
  cookidoo recipes saved [--human]
    List saved/bookmarked recipe collections
  
  cookidoo recipes search <query> [--human]
    Search recipes in your saved collections
  
  cookidoo meal-plan [week] [--human]
    Show meal plan (default: current week, or specify week offset like +1, -1)
  
  cookidoo meal-plan add <recipe-id> <date> [--human]
    Add a recipe to the meal plan (date format: YYYY-MM-DD)

Options:
  --human    Output in human-readable format instead of JSON
  --help     Show this help message

Examples:
  cookidoo shopping-list --human
  cookidoo shopping-list add "Tomatoes"
  cookidoo shopping-list check "Tomatoes"
  cookidoo recipes saved --human
  cookidoo meal-plan 0 --human
  cookidoo meal-plan add r59322 2026-02-16
""")


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]
    
    if not args or "--help" in args or "-h" in args:
        print_usage()
        sys.exit(0)
    
    # Check for --human flag
    human = "--human" in args
    if human:
        args = [arg for arg in args if arg != "--human"]
    
    if not args:
        print_usage()
        sys.exit(0)
    
    # Parse commands
    command = args[0]
    
    try:
        if command == "shopping-list":
            if len(args) == 1:
                asyncio.run(cmd_shopping_list(args, human))
            elif args[1] == "add" and len(args) >= 3:
                item_name = " ".join(args[2:])
                asyncio.run(cmd_shopping_list_add(item_name, args, human))
            elif args[1] == "check" and len(args) >= 3:
                item_name = " ".join(args[2:])
                asyncio.run(cmd_shopping_list_check(item_name, args, human))
            elif args[1] == "clear":
                asyncio.run(cmd_shopping_list_clear(args, human))
            else:
                print("Invalid shopping-list command", file=sys.stderr)
                print_usage()
                sys.exit(1)
        
        elif command == "recipes":
            if len(args) >= 2 and args[1] == "saved":
                asyncio.run(cmd_recipes_saved(args, human))
            elif len(args) >= 3 and args[1] == "search":
                query = " ".join(args[2:])
                asyncio.run(cmd_recipes_search(query, args, human))
            else:
                print("Invalid recipes command", file=sys.stderr)
                print_usage()
                sys.exit(1)
        
        elif command == "meal-plan":
            if len(args) == 1:
                asyncio.run(cmd_meal_plan(0, args, human))
            elif len(args) >= 2 and args[1] == "add" and len(args) >= 4:
                recipe_id = args[2]
                date_str = args[3]
                asyncio.run(cmd_meal_plan_add(recipe_id, date_str, args, human))
            elif len(args) >= 2 and args[1] not in ["add"]:
                # Week offset
                try:
                    week_offset = int(args[1])
                    asyncio.run(cmd_meal_plan(week_offset, args, human))
                except ValueError:
                    print(f"Invalid week offset: {args[1]}", file=sys.stderr)
                    sys.exit(1)
            else:
                print("Invalid meal-plan command", file=sys.stderr)
                print_usage()
                sys.exit(1)
        
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            print_usage()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
