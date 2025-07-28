# ~ test_enhanced_webuis.py | Test Enhanced WebUI Functionality ~

import sys
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent.parent / 'modules'))

def test_webui_utils():
    """Test enhanced webui_utils functionality."""
    
    print("🧪 Testing Enhanced WebUI Utils...")
    
    try:
        from webui_utils import (
            get_available_webuis, 
            get_webui_category,
            is_webui_supported,
            get_webui_features,
            WEBUI_PATHS,
            WEBUI_FEATURES
        )
        
        # Test basic functionality
        available_webuis = get_available_webuis()
        print(f"✅ Available WebUIs ({len(available_webuis)}): {available_webuis}")
        
        # Test each WebUI category
        categories = {}
        for webui in available_webuis:
            category = get_webui_category(webui)
            if category not in categories:
                categories[category] = []
            categories[category].append(webui)
        
        print("\n📊 WebUI Categories:")
        for category, webuis in categories.items():
            print(f"   {category}: {webuis}")
        
        # Test feature detection
        print("\n🔍 Feature Detection Tests:")
        test_cases = [
            ('A1111', 'models', True),
            ('ComfyUI', 'models', True),
            ('FaceFusion', 'models', False),
            ('RoopUnleashed', 'extensions', False),
            ('Forge', 'lora', True)
        ]
        
        for webui, feature, expected in test_cases:
            if webui in available_webuis:
                result = is_webui_supported(webui, feature)
                status = "✅" if result == expected else "❌"
                print(f"   {status} {webui} supports {feature}: {result} (expected {expected})")
        
        return True
        
    except Exception as e:
        print(f"❌ WebUI Utils test failed: {e}")
        return False

def test_webui_installer():
    """Test enhanced webui-installer functionality."""
    
    print("\n🧪 Testing Enhanced WebUI Installer...")
    
    try:
        # Import installer components
        installer_path = Path(__file__).parent / 'webui-installer.py'
        if not installer_path.exists():
            print("❌ webui-installer.py not found")
            return False
        
        # Read and verify installer content
        with open(installer_path, 'r') as f:
            content = f.read()
        
        # Check for enhanced features
        required_features = [
            'WEBUI_REPOSITORIES',
            'install_git_webui',
            'setup_webui_environment',
            'FaceFusion',
            'RoopUnleashed',
            'Forge'
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing features in installer: {missing_features}")
            return False
        
        print("✅ Enhanced WebUI Installer verified")
        return True
        
    except Exception as e:
        print(f"❌ WebUI Installer test failed: {e}")
        return False

def test_widgets():
    """Test enhanced widgets functionality."""
    
    print("\n🧪 Testing Enhanced Widgets...")
    
    try:
        widgets_path = Path(__file__).parent / 'widgets-en.py'
        if not widgets_path.exists():
            print("❌ widgets-en.py not found")
            return False
        
        # Read and verify widgets content
        with open(widgets_path, 'r') as f:
            content = f.read()
        
        # Check for enhanced features
        required_features = [
            'WEBUI_SELECTION',
            'enhanced_update_change_webui',
            'FaceFusion',
            'RoopUnleashed',
            'Forge',
            'ReForge',
            'SD-UX',
            'DreamO'
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing features in widgets: {missing_features}")
            return False
        
        print("✅ Enhanced Widgets verified")
        return True
        
    except Exception as e:
        print(f"❌ Widgets test failed: {e}")
        return False

def test_downloading():
    """Test enhanced downloading functionality."""
    
    print("\n🧪 Testing Enhanced Downloading...")
    
    try:
        downloading_path = Path(__file__).parent / 'downloading-en.py'
        if not downloading_path.exists():
            print("❌ downloading-en.py not found")
            return False
        
        # Read and verify downloading content
        with open(downloading_path, 'r') as f:
            content = f.read()
        
        # Check for enhanced features
        required_features = [
            'get_webui_category',
            'is_webui_supported',
            'WebUI-aware',
            'face_swap'
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing features in downloading: {missing_features}")
            return False
        
        print("✅ Enhanced Downloading verified")
        return True
        
    except Exception as e:
        print(f"❌ Downloading test failed: {e}")
        return False

def test_launch():
    """Test enhanced launch functionality."""
    
    print("\n🧪 Testing Enhanced Launch...")
    
    try:
        launch_path = Path(__file__).parent / 'launch.py'
        if not launch_path.exists():
            print("❌ launch.py not found")
            return False
        
        # Read and verify launch content
        with open(launch_path, 'r') as f:
            content = f.read()
        
        # Check for enhanced features
        required_features = [
            'WEBUI_LAUNCH_CONFIGS',
            'setup_facefusion',
            'setup_roop',
            'setup_forge',
            'FaceFusion',
            'RoopUnleashed'
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing features in launch: {missing_features}")
            return False
        
        print("✅ Enhanced Launch verified")
        return True
        
    except Exception as e:
        print(f"❌ Launch test failed: {e}")
        return False

def test_requirements_files():
    """Test that WebUI-specific requirements files exist."""
    
    print("\n🧪 Testing Requirements Files...")
    
    scripts_dir = Path(__file__).parent
    
    required_files = [
        'requirements_facefusion.txt',
        'requirements_roopunleashed.txt',
        'requirements_dreamo.txt',
        'requirements_forge.txt',
        'requirements_reforge.txt',
        'requirements_sd-ux.txt'
    ]
    
    missing_files = []
    for req_file in required_files:
        if not (scripts_dir / req_file).exists():
            missing_files.append(req_file)
    
    if missing_files:
        print(f"❌ Missing requirements files: {missing_files}")
        return False
    
    print("✅ All requirements files found")
    return True

def main():
    """Run all tests."""
    
    print("🚀 LightningSdaigen Enhanced WebUI Test Suite")
    print("=" * 60)
    
    tests = [
        ("WebUI Utils", test_webui_utils),
        ("WebUI Installer", test_webui_installer),
        ("Widgets", test_widgets),
        ("Downloading", test_downloading),
        ("Launch", test_launch),
        ("Requirements Files", test_requirements_files)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Enhanced WebUI system is ready.")
        print("\nNext steps:")
        print("1. Run the notebook and test WebUI selection")
        print("2. Try installing a new WebUI (Forge, RoopUnleashed, etc.)")
        print("3. Verify dynamic UI adaptation works")
    else:
        print("⚠️ Some tests failed. Please check the enhanced scripts installation.")
    
    return failed == 0

if __name__ == "__main__":
    main()
