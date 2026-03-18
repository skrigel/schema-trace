import requests
from typing import List, Dict, Any, Optional
from cli.config import CLIConfig


class SchemaTraceAPIError(Exception):
    """Custom exception for API errors"""
    pass


class APIClient:
    """
    HTTP client for SchemaTrace API.

    Handles authentication, error handling, and response parsing.
    All CLI commands use this client to communicate with the backend.

    Attributes:
        config: CLI configuration
        base_url: Base API URL (without trailing slash)
        session: Requests session with persistent headers
    """

    def __init__(self, config: CLIConfig):
        self.config = config
        self.base_url = config.api_url.rstrip('/')
        self.session = requests.Session()

        # Set API key header if configured
        if config.api_key:
            self.session.headers.update({"X-API-Key": config.api_key})

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/projects/")
            **kwargs: Additional arguments passed to requests

        Returns:
            Response object

        Raises:
            SchemaTraceAPIError: On any request failure
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            # Parse error message from API response
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = str(e)

            raise SchemaTraceAPIError(f"API Error: {error_detail}") from e

        except requests.exceptions.ConnectionError as e:
            raise SchemaTraceAPIError(
                f"Cannot connect to API at {self.base_url}. "
                f"Is the server running?"
            ) from e

        except requests.exceptions.Timeout as e:
            raise SchemaTraceAPIError("API request timed out") from e

    # Project endpoints

    def create_project(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name (must be unique)
            description: Optional project description

        Returns:
            Created project data
        """
        response = self._request(
            "POST",
            "/projects/",
            json={"name": name, "description": description}
        )
        return response.json()

    def get_project_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get project by name.

        Args:
            name: Project name

        Returns:
            Project data
        """
        response = self._request("GET", f"/projects/by-name/{name}")
        return response.json()

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.

        Returns:
            List of project data
        """
        response = self._request("GET", "/projects/")
        return response.json()

    # Model endpoints

    def create_model(
        self,
        project_id: int,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new model.

        Args:
            project_id: ID of the project this model belongs to
            name: Model name (e.g., "User", "Post")
            description: Optional model description

        Returns:
            Created model data
        """
        response = self._request(
            "POST",
            "/models/",
            json={
                "project_id": project_id,
                "name": name,
                "description": description
            }
        )
        return response.json()

    def get_model(self, model_id: int) -> Dict[str, Any]:
        """
        Get model by ID.

        Args:
            model_id: Model ID

        Returns:
            Model data
        """
        response = self._request("GET", f"/models/{model_id}")
        return response.json()

    def list_models(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List models, optionally filtered by project.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            List of model data
        """
        params = {"project_id": project_id} if project_id else {}
        response = self._request("GET", "/models/", params=params)
        return response.json()

    # Event endpoints

    def upload_events_bulk(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk upload schema events.

        This is the primary endpoint used by the scan command.

        Args:
            events: List of event data (SchemaEventCreate format)

        Returns:
            Bulk upload response with created_count and events
        """
        response = self._request(
            "POST",
            "/events/bulk",
            json={"events": events}
        )
        return response.json()

    def list_model_events(self, model_id: int) -> List[Dict[str, Any]]:
        """
        Get all events for a model.

        Args:
            model_id: Model ID

        Returns:
            List of events in chronological order
        """
        response = self._request("GET", f"/events/model/{model_id}")
        return response.json()
