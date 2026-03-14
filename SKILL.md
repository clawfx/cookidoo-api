# Cookidoo CLI Skill

Interact with the Cookidoo recipe platform (Thermomix) to manage shopping lists, recipes, and meal planning.

## What is Cookidoo?

Cookidoo is the official recipe platform for Thermomix cooking appliances. It provides access to thousands of recipes, meal planning features, and automated shopping lists based on planned recipes.

## Features

- 🛒 **Shopping List Management** - View, add, check off, and clear items
- 📚 **Recipe Collections** - Browse saved and bookmarked recipe collections
- 🔍 **Recipe Search** - Search through your saved collections
- 📅 **Meal Planning** - View and manage weekly meal plans
- 🤖 **Automation-friendly** - JSON output for programmatic use

## Setup

### Prerequisites

- Python 3.7 or higher
- Cookidoo account with valid credentials
- Internet connection

### Installation

The skill uses a Python virtual environment with the `cookidoo-api` library installed:

```bash
cd skills/cookidoo
python3 -m venv venv
./venv/bin/pip install cookidoo-api python-dotenv
```

### Credentials

Store your Cookidoo credentials in `credentials.env` at the workspace root:

```bash
# Cookidoo (Thermomix)
COOKIDOO_EMAIL=your@email.com
COOKIDOO_PASSWORD=yourpassword
COOKIDOO_COUNTRY=de-AT
```

**Supported country codes:**
- `de-AT` (Austria, German)
- `de-DE` (Germany, German)
- `en-GB` (United Kingdom, English)
- `en-US` (USA, English)
- `fr-FR` (France, French)
- And many more...

## Usage

All commands support two output formats:
- **JSON** (default) - For programmatic use
- **Human-readable** - Add `--human` flag for pretty-printed output

### Shopping List

**List all items:**
```bash
./cookidoo.sh shopping-list
./cookidoo.sh shopping-list --human
```

Shows both recipe ingredients (from planned recipes) and additional purchases with their checked status.

**Add an item:**
```bash
./cookidoo.sh shopping-list add "Tomatoes"
./cookidoo.sh shopping-list add "Olive Oil" --human
```

Adds items to the "additional purchases" section of your shopping list.

**Check/uncheck an item:**
```bash
./cookidoo.sh shopping-list check "Tomatoes"
./cookidoo.sh shopping-list check "Milk" --human
```

Toggles the checked status of an item. Supports partial matching (case-insensitive).

**Clear the entire list:**
```bash
./cookidoo.sh shopping-list clear
./cookidoo.sh shopping-list clear --human
```

Removes all items from the shopping list (both ingredients and additional items).

### Recipes

**List saved collections:**
```bash
./cookidoo.sh recipes saved
./cookidoo.sh recipes saved --human
```

Shows your saved/bookmarked recipe collections (both managed and custom).

**Search recipes:**
```bash
./cookidoo.sh recipes search "pasta"
./cookidoo.sh recipes search "chicken soup" --human
```

Searches through your saved recipe collections. Note: The Cookidoo API doesn't provide full-text recipe search, so this searches collection names only.

### Meal Planning

**View current week's meal plan:**
```bash
./cookidoo.sh meal-plan
./cookidoo.sh meal-plan 0 --human
```

**View next/previous weeks:**
```bash
./cookidoo.sh meal-plan 1 --human    # Next week
./cookidoo.sh meal-plan -1 --human   # Last week
./cookidoo.sh meal-plan 2            # Two weeks ahead
```

**Add a recipe to the meal plan:**
```bash
./cookidoo.sh meal-plan add r59322 2026-02-16
./cookidoo.sh meal-plan add r907015 2026-02-20 --human
```

Recipe IDs can be found in your saved collections or from the Cookidoo website URL.

## Output Examples

### JSON (default)
```json
{
  "ingredients": [
    {
      "id": "ing-123",
      "name": "Flour",
      "quantity": "500g",
      "checked": false
    }
  ],
  "additional": [
    {
      "id": "add-456",
      "name": "Milk",
      "checked": true
    }
  ]
}
```

### Human-readable (`--human`)
```
🛒 Shopping List

📝 Recipe Ingredients:
  ⬜ Flour (500g)
  ⬜ Eggs (3 pieces)

➕ Additional Items:
  ✅ Milk
  ⬜ Bread
```

## API Library

This skill uses the [`cookidoo-api`](https://github.com/miaucl/cookidoo-api) Python library, which is an unofficial API wrapper for Cookidoo. It's installed in a virtual environment for easy updates:

```bash
cd skills/cookidoo
./venv/bin/pip install --upgrade cookidoo-api
```

## Limitations

- **No full-text search:** The API doesn't support searching all Cookidoo recipes, only your saved collections
- **Premium features:** Some features may require an active Cookidoo subscription
- **Rate limiting:** Excessive API calls may be throttled by Cookidoo servers
- **Unofficial API:** This uses a reverse-engineered API and may break if Cookidoo changes their backend

## Troubleshooting

**Authentication errors:**
- Verify your email and password in `credentials.env`
- Check that your Cookidoo account is active
- Try logging in via the website to ensure your credentials work

**Localization errors:**
- Ensure `COOKIDOO_COUNTRY` is set to a valid country code
- Try common codes like `de-AT`, `de-DE`, `en-GB`, or `en-US`

**Virtual environment missing:**
```bash
cd skills/cookidoo
python3 -m venv venv
./venv/bin/pip install cookidoo-api python-dotenv
```

## Integration Examples

**Get shopping list in a script:**
```bash
ITEMS=$(./cookidoo.sh shopping-list | jq -r '.ingredients[].name')
echo "$ITEMS"
```

**Add multiple items:**
```bash
for item in "Butter" "Sugar" "Vanilla"; do
  ./cookidoo.sh shopping-list add "$item"
done
```

**Check what's for dinner this week:**
```bash
./cookidoo.sh meal-plan --human | grep -A 10 "$(date +%A)"
```

## Privacy & Security

- Credentials are stored locally in `credentials.env` (never committed to git)
- All API communication is done via HTTPS
- No telemetry or tracking beyond what Cookidoo's official API requires
- The skill does not share your data with third parties

## Credits

- **Cookidoo API Library:** [miaucl/cookidoo-api](https://github.com/miaucl/cookidoo-api)
- **Platform:** Cookidoo by Vorwerk (official Thermomix recipe platform)

## Disclaimer

This is an unofficial tool and is not endorsed by or affiliated with Cookidoo, Vorwerk, or Thermomix. Use at your own risk.
