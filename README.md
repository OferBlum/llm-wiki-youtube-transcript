# LLM Wiki & YouTube Knowledge Ingestion System

This repository implements a variation of the Karpathy method for building an LLM-managed Wikipedia inside an Obsidian Vault, integrated with automated YouTube video transcription.

## Overview
The system allows you to automatically ingest raw knowledge, specifically YouTube videos, transcribe them, and resolve them into interconnected wiki pages. This turns raw information streams into structured, permanent knowledge.

## Files included:
- `SKILL-ingest.md`: The agent skill responsible for ingesting new sources into the raw processing pipeline.
- `SKILL-resolve.md`: The agent skill responsible for resolving processed/raw information into permanent, interconnected wiki notes.
- `youtube-fetch.py`: A Python script that fetches and transcribes YouTube videos automatically, preparing them for the ingestion pipeline.
- `youtube_queue/md`: The pending/compiled youtube videos

## Usage
1. Setup the Python environment to run `youtube-fetch.py`.
2. Add the skill files to your agent's system prompt directory.
3. Queue YouTube videos using the Python script, and prompt the agent to ingest and resolve the new information into your Vault's wiki section.
