"""Main Entry Point"""
import argparse
from src.data_fetcher.nse_fetcher import NSEBhavcopyFetcher
from src.analyzers.options_analyzer import OptionsAnalyzer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['fetch', 'analyze', 'dashboard'])
    args = parser.parse_args()
    
    if args.mode == 'fetch':
        fetcher = NSEBhavcopyFetcher()
        fetcher.fetch_latest()

if __name__ == '__main__':
    main()
