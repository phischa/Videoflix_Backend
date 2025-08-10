def test_email_service(send_test_email: bool = True, recipient: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive test function for email service
    
    Args:
        send_test_email: Whether to actually send a test email
        recipient: Email address to send test to (defaults to DEFAULT_FROM_EMAIL)
        
    Returns:
        Dict[str, Any]: Test results and information
    """
    results = {
        'timestamp': time.time(),
        'django_debug': settings.DEBUG,
        'tests': {},
        'summary': 'Unknown'
    }
    
    print("🧪 EMAIL SERVICE TEST")
    print("=" * 50)
    
    # Test 1: Configuration Check
    print("1️⃣ Testing configuration...")
    try:
        config = EmailConfig.from_settings()
        is_valid, errors = validate_email_config()
        
        results['tests']['configuration'] = {
            'status': 'PASS' if is_valid else 'FAIL',
            'errors': errors,
            'config': {
                'email_backend': settings.EMAIL_BACKEND,
                'from_email': config.from_email,
                'use_async': config.use_async,
                'max_retries': config.max_retries,
            }
        }
        
        if is_valid:
            print("   ✅ Configuration valid")
            print(f"   📧 From: {config.from_email}")
            print(f"   🔧 Backend: {settings.EMAIL_BACKEND}")
        else:
            print("   ❌ Configuration errors:")
            for error in errors:
                print(f"      - {error}")
                
    except Exception as e:
        results['tests']['configuration'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        print(f"   ❌ Configuration test failed: {e}")
    
    # Test 2: SMTP Connection (only if not console backend)
    print("\n2️⃣ Testing SMTP connection...")
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("   ⚠️  Using console backend (development mode)")
        results['tests']['smtp_connection'] = {
            'status': 'SKIP',
            'reason': 'Console backend in use'
        }
    else:
        try:
            from django.core.mail import get_connection
            connection = get_connection()
            connection.open()
            connection.close()
            
            print("   ✅ SMTP connection successful")
            results['tests']['smtp_connection'] = {
                'status': 'PASS',
                'host': getattr(settings, 'EMAIL_HOST', 'Unknown'),
                'port': getattr(settings, 'EMAIL_PORT', 'Unknown'),
            }
            
        except Exception as e:
            print(f"   ❌ SMTP connection failed: {e}")
            results['tests']['smtp_connection'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    
    # Test 3: Template Rendering
    print("\n3️⃣ Testing template rendering...")
    try:
        service = ActivationEmailService()
        
        # Create dummy context
        from django.contrib.auth.models import User
        dummy_user = User(email="test@example.com", id=999)
        context = service._get_base_context()
        context.update({
            'user': dummy_user,
            'activation_url': 'https://example.com/activate/test/token/',
            'expiry_hours': 24
        })
        
        # Try to render templates (with fallbacks)
        text_content = service._render_template_safe(
            'emails/activation_email.txt', 
            context,
            service.TEXT_FALLBACK.format(**context)
        )
        html_content = service._render_template_safe(
            'emails/activation_email.html',
            context, 
            service.HTML_FALLBACK.format(**context)
        )
        
        print("   ✅ Template rendering successful")
        print(f"   📝 Text length: {len(text_content)} chars")
        print(f"   🌐 HTML length: {len(html_content)} chars")
        
        results['tests']['template_rendering'] = {
            'status': 'PASS',
            'text_length': len(text_content),
            'html_length': len(html_content)
        }
        
    except Exception as e:
        print(f"   ❌ Template rendering failed: {e}")
        results['tests']['template_rendering'] = {
            'status': 'FAIL',
            'error': str(e)
        }
    
    # Test 4: Send Test Email (optional)
    if send_test_email:
        print("\n4️⃣ Sending test email...")
        
        if not recipient:
            recipient = config.from_email
        
        try:
            # Create test email
            from django.core.mail import EmailMultiAlternatives
            
            subject = f"[Videoflix Test] Email Service Test - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            text_content = f"""
Videoflix Email Service Test

This is a test email to verify your email configuration.

Test Details:
- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Django DEBUG: {settings.DEBUG}
- Email Backend: {settings.EMAIL_BACKEND}
- From: {config.from_email}
- To: {recipient}

If you received this email, your email service is working correctly!

--
Videoflix Team
"""
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head><title>Videoflix Email Test</title></head>
<body>
<h2>🧪 Videoflix Email Service Test</h2>
<p>This is a test email to verify your email configuration.</p>

<h3>Test Details:</h3>
<ul>
<li><strong>Timestamp:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</li>
<li><strong>Django DEBUG:</strong> {settings.DEBUG}</li>
<li><strong>Email Backend:</strong> {settings.EMAIL_BACKEND}</li>
<li><strong>From:</strong> {config.from_email}</li>
<li><strong>To:</strong> {recipient}</li>
</ul>

<p>✅ <strong>If you received this email, your email service is working correctly!</strong></p>

<hr>
<p><em>Videoflix Team</em></p>
</body>
</html>
"""
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=config.from_email,
                to=[recipient]
            )
            email.attach_alternative(html_content, "text/html")
            
            start_time = time.time()
            email.send()
            duration = time.time() - start_time
            
            print(f"   ✅ Test email sent successfully!")
            print(f"   📧 To: {recipient}")
            print(f"   ⏱️  Duration: {duration:.2f}s")
            
            results['tests']['test_email'] = {
                'status': 'PASS',
                'recipient': recipient,
                'duration': duration,
                'subject': subject
            }
            
        except Exception as e:
            print(f"   ❌ Test email failed: {e}")
            results['tests']['test_email'] = {
                'status': 'FAIL',
                'error': str(e),
                'recipient': recipient
            }
    else:
        print("\n4️⃣ Skipping test email (send_test_email=False)")
        results['tests']['test_email'] = {
            'status': 'SKIP',
            'reason': 'Disabled by parameter'
        }
    
    # Summary
    print("\n" + "=" * 50)
    
    # Calculate overall status
    statuses = [test.get('status', 'UNKNOWN') for test in results['tests'].values()]
    if any(status == 'FAIL' for status in statuses):
        overall_status = 'SOME TESTS FAILED'
        print("❌ OVERALL RESULT: SOME TESTS FAILED")
    elif any(status == 'ERROR' for status in statuses):
        overall_status = 'ERRORS ENCOUNTERED'
        print("⚠️  OVERALL RESULT: ERRORS ENCOUNTERED")
    elif all(status in ['PASS', 'SKIP'] for status in statuses):
        overall_status = 'ALL TESTS PASSED'
        print("✅ OVERALL RESULT: ALL TESTS PASSED")
    else:
        overall_status = 'UNKNOWN STATUS'
        print("❓ OVERALL RESULT: UNKNOWN STATUS")
    
    results['summary'] = overall_status
    
    # Next steps
    if overall_status == 'ALL TESTS PASSED':
        print("\n🚀 NEXT STEPS:")
        print("   1. Your email service is ready!")
        print("   2. Test user registration/password reset")
        print("   3. Configure RQ workers for async emails")
    else:
        print("\n🔧 TROUBLESHOOTING:")
        if any(test.get('status') == 'FAIL' for test in results['tests'].values() if 'smtp' in str(test)):
            print("   - Check your SMTP settings in .env")
            print("   - Verify email host, port, username, password")
            print("   - Check if your email provider requires app passwords")
    
    return results
    