import sqlite3
import time
import hashlib
from datetime import datetime
import json

# Simulated fingerprint device class (for development/testing)
class FingerprintSimulator:
    """Simulates fingerprint scanner for development"""
    
    def __init__(self):
        self.templates = {}
        self.next_id = 1
    
    def verify_fingerprint(self):
        """Simulate fingerprint verification"""
        # In real implementation, this would read from actual scanner
        time.sleep(1)  # Simulate scanning delay
        return {
            'success': True,
            'verified': True,
            'fingerprint_id': 1,
            'confidence': 95
        }
    
    def enroll_fingerprint(self, card_number, name):
        """Simulate fingerprint enrollment"""
        time.sleep(2)  # Simulate enrollment delay
        
        # Generate unique fingerprint ID based on card number
        fingerprint_id = self.next_id
        template = hashlib.sha256(f"{card_number}{name}{datetime.now()}".encode()).hexdigest()
        
        self.templates[card_number] = {
            'fingerprint_id': fingerprint_id,
            'template': template,
            'card_number': card_number,
            'name': name,
            'enrolled_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.next_id += 1
        
        return {
            'success': True,
            'message': f'Fingerprint enrolled for {name}',
            'fingerprint_id': fingerprint_id,
            'template': template
        }
    
    def verify_by_card(self, card_number):
        """Verify fingerprint for specific card"""
        if card_number in self.templates:
            time.sleep(1)
            return {
                'success': True,
                'verified': True,
                'card_number': card_number,
                'name': self.templates[card_number]['name'],
                'confidence': 98
            }
        return {'success': False, 'verified': False, 'error': 'No fingerprint enrolled'}

# Real fingerprint scanner integration (commented out for development)
"""
from pyfingerprint.pyfingerprint import PyFingerprint

class FingerprintScanner:
    def __init__(self, port='/dev/ttyUSB0', baudrate=57600):
        try:
            self.f = PyFingerprint(port, baudrate)
            if not self.f.verifyPassword():
                raise ValueError('Wrong fingerprint sensor password')
        except Exception as e:
            print(f"Error initializing fingerprint scanner: {e}")
            raise
    
    def enroll(self, position_number=None):
        try:
            print('Waiting for finger...')
            while not self.f.readImage():
                pass
            
            self.f.convertImage(0x01)
            result = self.f.searchTemplate()
            position_number = result[0]
            
            if position_number >= 0:
                return {'success': False, 'error': 'Template already exists'}
            
            print('Remove finger...')
            time.sleep(2)
            
            print('Place same finger again...')
            while not self.f.readImage():
                pass
            
            self.f.convertImage(0x02)
            
            if self.f.compareCharacteristics() == 0:
                return {'success': False, 'error': 'Fingers do not match'}
            
            self.f.createTemplate()
            
            if position_number is None:
                position_number = self.f.getTemplateCount()
            
            self.f.storeTemplate(position_number, 0x01)
            
            # Get template as bytes
            template = self.f.downloadCharacteristics(0x01)
            
            return {
                'success': True,
                'position': position_number,
                'template': template
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify(self):
        try:
            print('Waiting for finger...')
            while not self.f.readImage():
                pass
            
            self.f.convertImage(0x01)
            result = self.f.searchTemplate()
            
            position_number = result[0]
            accuracy = result[1]
            
            if position_number == -1:
                return {'success': False, 'verified': False}
            
            return {
                'success': True,
                'verified': True,
                'position': position_number,
                'accuracy': accuracy
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
"""

class BiometricAuth:
    """Main biometric authentication class"""
    
    def __init__(self, use_simulator=True):
        self.use_simulator = use_simulator
        
        if use_simulator:
            self.scanner = FingerprintSimulator()
        else:
            # Uncomment for real scanner
            # self.scanner = FingerprintScanner()
            pass
        
        self.db = sqlite3.connect('database.db')
        self.db.row_factory = sqlite3.Row
    
    def register_fingerprint(self, card_number, name):
        """Register fingerprint for a user"""
        
        # Check if already registered
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM biometrics WHERE card_number = ? AND is_active = 1",
            (card_number,)
        )
        existing = cursor.fetchone()
        
        if existing:
            return {
                'success': False,
                'message': 'Fingerprint already registered for this card'
            }
        
        # Simulate/enroll fingerprint
        result = self.scanner.enroll_fingerprint(card_number, name)
        
        if result['success']:
            # Store in database
            cursor.execute('''
                INSERT INTO biometrics 
                (card_number, fingerprint_template, fingerprint_id, registered_date, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                card_number,
                result['template'],
                result['fingerprint_id'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                1
            ))
            
            self.db.commit()
            
            return {
                'success': True,
                'message': result['message'],
                'fingerprint_id': result['fingerprint_id']
            }
        
        return result
    
    def verify_fingerprint(self, card_number=None):
        """Verify fingerprint"""
        
        if card_number:
            # Verify for specific card number
            result = self.scanner.verify_by_card(card_number)
        else:
            # General verification
            result = self.scanner.verify_fingerprint()
        
        if result.get('verified'):
            # Update last used timestamp
            cursor = self.db.cursor()
            cursor.execute('''
                UPDATE biometrics 
                SET last_used = ?
                WHERE card_number = ?
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                result.get('card_number', '')
            ))
            self.db.commit()
        
        return result
    
    def get_biometric_status(self, card_number):
        """Get biometric registration status"""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM biometrics WHERE card_number = ? AND is_active = 1",
            (card_number,)
        )
        biometric = cursor.fetchone()
        
        if biometric:
            return {
                'registered': True,
                'registered_date': biometric['registered_date'],
                'last_used': biometric['last_used'],
                'fingerprint_id': biometric['fingerprint_id']
            }
        
        return {'registered': False}
    
    def delete_fingerprint(self, card_number):
        """Delete fingerprint registration"""
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE biometrics SET is_active = 0 WHERE card_number = ?",
            (card_number,)
        )
        self.db.commit()
        
        return cursor.rowcount > 0
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()