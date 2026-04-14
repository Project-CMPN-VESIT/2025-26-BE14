from django.shortcuts import render
import json

from .gemini import rank_products
from .scrapers.amazon import scrape_amazon_products
from .scrapers.flipkart import scrape_flipkart_products


def home(request):
    return render(request, "index.html")


def analyze(request):
    if request.method != "POST":
        return render(request, "index.html")

    query = request.POST.get("product")

    # 1️⃣ Scrape Amazon
    amazon_products = scrape_amazon_products(query, limit=3)

    # 2️⃣ Scrape Flipkart
    flipkart_products = scrape_flipkart_products(query, limit=3)

    # 3️⃣ Merge results
    all_products = amazon_products + flipkart_products

    # 4️⃣ Rank using Gemini
    ranked_json = rank_products(all_products)

    ranked_products = json.loads(ranked_json)

    # 5️⃣ Render results
    return render(request, "results.html", {
        "data": ranked_products
    })
