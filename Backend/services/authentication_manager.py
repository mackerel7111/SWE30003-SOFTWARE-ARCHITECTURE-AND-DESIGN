import logging
from datetime import datetime, timezone
from Backend.database import Database
from Backend.models import (
    PetOwner, AssociationStaff, VeterinaryPartner, PetProfile,
    Symptom, FirstAidGuide, InstructionalVideo, VetDetails,
    RegionalAlert, ApprovalRequest, EducationalQuiz, QuizQuestion, QuizFeedback,
    ROLE_PET_OWNER, ROLE_ASSOCIATION_STAFF, ROLE_VET_PARTNER,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
)

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """
    Singleton Control class responsible for managing user sessions,
    authentication verification, and role-based access control (RBAC).
    """
    
    _instance = None

    def __new__(cls) -> "AuthenticationManager":
        """Enforce the Singleton pattern for the AuthenticationManager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db = Database()
        return cls._instance

    def authenticateUser(self, email: str, passwordPlain: str) -> dict | None:
        """
        Validate user credentials against stored records.
        
        Note: For this prototype implementation, a simplified plaintext check 
        is carried out. In a final production setup, this would use a secure 
        hashing library like bcrypt.

        Parameters
        ----------
        email : str
        passwordPlain : str

        Returns
        -------
        dict or None
            A session state dictionary containing basic user identity and role 
            if authentication is successful; None otherwise.
        """
        userDoc = self._db.findUserByEmail(email)
        if not userDoc or not userDoc.get("isActive"):
            return None

        # Prototype fallback password verification match
        if userDoc.get("passwordHash") == f"hashed_{passwordPlain}_placeholder" or userDoc.get("passwordHash") == passwordPlain:
            return {
                "userId": str(userDoc["_id"]),
                "email": userDoc["email"],
                "role": userDoc["role"],
                "fullName": userDoc["fullName"]
            }
        return None

    def verifyRole(self, sessionUser: dict | None, requiredRoles: list[str]) -> bool:
        """
        Enforce Role-Based Access Control (RBAC) constraints on a session user.

        Parameters
        ----------
        sessionUser : dict or None
            The current active session user details payload.
        requiredRoles : list[str]
            A collection of role identifiers authorized to perform an operation.

        Returns
        -------
        bool
            True if the user session is active and possesses a required role; 
            False otherwise.
        """
        if not sessionUser:
            return False
        return sessionUser.get("role") in requiredRoles
