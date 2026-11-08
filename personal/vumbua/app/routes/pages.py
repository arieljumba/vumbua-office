from __future__ import annotations

from flask import Blueprint, Response, render_template

bp = Blueprint("pages", __name__)


@bp.get("/")
def home():
    return render_template("home.html", page="home")


@bp.get("/program")
def program():
    return render_template("program.html", page="program")


@bp.get("/robots.txt")
def robots():
    return Response(
        "User-agent: *\nAllow: /\nSitemap: https://vumbua.co.ke/sitemap.xml\n",
        mimetype="text/plain",
    )


@bp.get("/sitemap.xml")
def sitemap():
    locations = (
        "https://vumbua.co.ke/",
        "https://vumbua.co.ke/program",
        "https://vumbua.co.ke/market-insights",
        "https://vumbua.co.ke/contact",
    )
    entries = "".join(f"<url><loc>{location}</loc></url>" for location in locations)
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}</urlset>",
        mimetype="application/xml",
    )
