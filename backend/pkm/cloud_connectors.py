from langchain_community.document_loaders import GoogleDriveLoader

# TODO: Requires Google Cloud credentials and user authorization to run.

class PKMConnector:
    @staticmethod
    def load_google_drive_files(folder_id: str, credentials_path: str):
        """
        Loads all documents from a specified Google Drive folder.
        """
        try:
            loader = GoogleDriveLoader(
                folder_id=folder_id,
                # Specify the path to your service account or token file
                credentials_path=credentials_path, 
                recursive=True
            )
            # Returns a list of LangChain Document objects
            return loader.load()
        except Exception as e:
            print(f"Error loading Google Drive: {e}")
            return []