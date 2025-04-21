"""
This module provides a compatibility layer for PyQtWebEngine
Import this instead of directly importing from PyQt5.QtWebEngineWidgets

If PyQtWebEngine is not available, it will gracefully fail and provide 
a simple fallback that can at least let the application start.
"""

import logging
logger = logging.getLogger("WebEngineWrapper")

try:
    # Try to import the real QWebEngineView
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
    logger.info("Successfully imported PyQtWebEngineWidgets")
    HAS_WEBENGINE = True
except ImportError:
    # If not available, create a minimal stub
    from PyQt5.QtWidgets import QLabel
    logger.warning("PyQtWebEngineWidgets not available - using fallback")
    HAS_WEBENGINE = False
    
    # Create a stub QWebEngineView class
    class QWebEngineView(QLabel):
        """Fallback when QWebEngineView is not available"""
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setText("QWebEngineView not available.\nPlease install PyQtWebEngine with:\npip install PyQtWebEngine")
            self.setStyleSheet("background-color: #f0f0f0; padding: 20px; font-family: Arial; font-size: 14px;")
        
        def load(self, url):
            """Stub for load method"""
            self.setText(f"{self.text()}\n\nWould load: {url}")
            
        def setHtml(self, html):
            """Stub for setHtml method"""
            self.setText(f"{self.text()}\n\nWould display HTML content ({len(html)} bytes)")
            
        def page(self):
            """Stub for page method"""
            return FallbackPage()
            
    class FallbackPage:
        """Fallback page object"""
        
        def setWebChannel(self, channel):
            """Stub for setWebChannel method"""
            pass
            
    class QWebEngineSettings:
        """Stub for QWebEngineSettings"""
        
        JavascriptEnabled = "JavascriptEnabled"
        LocalContentCanAccessRemoteUrls = "LocalContentCanAccessRemoteUrls"
        XSSAuditingEnabled = "XSSAuditingEnabled"
        
        @staticmethod
        def setAttribute(attr, value):
            """Stub for setAttribute"""
            pass

# Export the classes
__all__ = ["QWebEngineView", "QWebEngineSettings", "HAS_WEBENGINE"]