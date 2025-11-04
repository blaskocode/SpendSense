"""Data validation for SpendSense"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime

from ..utils.errors import ValidationError
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DataValidator:
    """Validates data integrity and schema compliance"""
    
    @staticmethod
    def validate_user(user: Dict[str, Any]) -> bool:
        """Validate user data"""
        required_fields = ['user_id', 'created_at']
        
        for field in required_fields:
            if field not in user:
                raise ValidationError(f"User missing required field: {field}")
        
        if not isinstance(user['user_id'], str) or not user['user_id']:
            raise ValidationError("user_id must be a non-empty string")
        
        return True
    
    @staticmethod
    def validate_account(account: Dict[str, Any]) -> bool:
        """Validate account data"""
        required_fields = ['account_id', 'user_id', 'type']
        
        for field in required_fields:
            if field not in account:
                raise ValidationError(f"Account missing required field: {field}")
        
        valid_types = ['depository', 'credit']
        if account['type'] not in valid_types:
            raise ValidationError(f"Account type must be one of: {valid_types}")
        
        if account['balance_current'] is not None and account['balance_current'] < 0:
            if account['type'] == 'depository':
                logger.warning(f"Negative balance for depository account: {account['account_id']}")
        
        return True
    
    @staticmethod
    def validate_transaction(transaction: Dict[str, Any]) -> bool:
        """Validate transaction data"""
        required_fields = ['transaction_id', 'account_id', 'date', 'amount']
        
        for field in required_fields:
            if field not in transaction:
                raise ValidationError(f"Transaction missing required field: {field}")
        
        if not isinstance(transaction['amount'], (int, float)):
            raise ValidationError("Transaction amount must be numeric")
        
        return True
    
    @staticmethod
    def validate_liability(liability: Dict[str, Any]) -> bool:
        """Validate liability data"""
        required_fields = ['liability_id', 'account_id', 'type']
        
        for field in required_fields:
            if field not in liability:
                raise ValidationError(f"Liability missing required field: {field}")
        
        valid_types = ['credit_card', 'mortgage', 'student_loan']
        if liability['type'] not in valid_types:
            raise ValidationError(f"Liability type must be one of: {valid_types}")
        
        if liability.get('apr') is not None:
            if not (0 <= liability['apr'] <= 100):
                raise ValidationError("APR must be between 0 and 100")
        
        return True
    
    @staticmethod
    def validate_batch(data: List[Dict[str, Any]], data_type: str) -> bool:
        """Validate a batch of data"""
        validators = {
            'user': DataValidator.validate_user,
            'account': DataValidator.validate_account,
            'transaction': DataValidator.validate_transaction,
            'liability': DataValidator.validate_liability,
        }
        
        if data_type not in validators:
            raise ValidationError(f"Unknown data type: {data_type}")
        
        validator = validators[data_type]
        errors = []
        
        for i, item in enumerate(data):
            try:
                validator(item)
            except ValidationError as e:
                errors.append(f"Item {i}: {str(e)}")
        
        if errors:
            raise ValidationError(f"Validation failed:\n" + "\n".join(errors))
        
        logger.info(f"Validated {len(data)} {data_type} records")
        return True

