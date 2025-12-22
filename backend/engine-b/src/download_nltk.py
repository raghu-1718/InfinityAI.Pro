import nltk
import sys

def download_nltk_data():
    packages = ["punkt", "punkt_tab", "stopwords", "vader_lexicon"]
    failed = []
    
    print("Downloading NLTK data...")
    for pkg in packages:
        try:
            print(f"Downloading {pkg}...")
            nltk.download(pkg, quiet=True)
            print(f"Successfully downloaded {pkg}")
        except Exception as e:
            print(f"Failed to download {pkg}: {e}")
            failed.append(pkg)
            
    if failed:
        print(f"Failed to download packages: {failed}")
        # Don't fail the build for this, as it might handle runtime downloads or be optional
        # sys.exit(1) 
    else:
        print("All NLTK packages downloaded successfully")

if __name__ == "__main__":
    download_nltk_data()
