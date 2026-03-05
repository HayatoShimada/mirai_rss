# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mirai_rss is a Python tool that fetches RSS feeds related to Toyama Prefecture Nanto City and posts them to a Discord server via WebHook. It targets the Mirai Shopkeeper Association (ミライ店主会) Discord server. The Gemini API is used to summarize fetched content.

## Tech Stack

- **Language:** Python
- **Libraries:** requests, feedparser, Gemini API
- **Deployment:** GitHub Actions (scheduled daily at 4:00 JST)

## Architecture

- Periodically fetches RSS feeds from configured URLs
- Detects new articles and posts them to Discord via WebHook
- Uses Gemini API to summarize article content
- RSS sources focus on: subsidy info, legal info, real estate, Toyama events, Nanto City news

## Language

Design documents and comments are in Japanese. Follow this convention.
