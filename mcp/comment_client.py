from config import settings
import requests
import logging

logging.basicConfig(level=logging.INFO)

class CommentClient:
    _instance = None

    def __new__(cls, token):
        if cls._instance is None:
            cls._instance = super(CommentClient, cls).__new__(cls)
            cls._instance.base_url = settings.COMMENT_BASE_URL
            cls._instance.token = token
        return cls._instance
    
    def fetch_comments(self, entity_id):
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.get(
            f"{self.base_url}/api/v1/comments/?entity_id={entity_id}",
            headers=headers
        )
        
        return response.text
    
