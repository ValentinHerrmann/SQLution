from django.http import HttpResponse
from django.shortcuts import render
from myapp.utils.qr import *
from myapp import views_user
from myapp.utils.decorators import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import logout


def qr_generator(request):
    svg_content = None
    download_ready = False
    form = QRGeneratorForm()
    logo_info = None
    logo_option = 'dataspark'  # Default value
    
    if request.method == 'POST':
        download_request = request.POST.get('download')
        
        if download_request:
            # Handle download request - recreate QR code from hidden fields
            content = request.POST.get('qr_content')
            logo_option = request.POST.get('logo_option', 'dataspark')
            qr_color = request.POST.get('qr_color', '#000000')
            background_type = request.POST.get('background_type', 'transparent')
            shape_type = 'square'  # Fixed to square since shape option is removed
            frame_type = request.POST.get('frame_type', 'rounded')
            frame_color = request.POST.get('frame_color', '#000000')
            download_format = request.POST.get('download_format', 'svg')
            
            # Convert background_type to background_color
            background_color = '#ffffff' if background_type == 'white' else '#ffffff'
            use_white_bg = background_type == 'white'
            
            if content:
                # Process logo based on selection for download - ensure download always works
                logo_info = None
                try:
                    if logo_option == 'dataspark':
                        logo_info = process_logo_for_qr()
                        # If logo processing fails, continue without logo
                        if logo_info is None:
                            pass  # Continue without logo
                    # For custom uploads, we can't recreate them on download, so skip them
                    # For 'none' logo option, logo_info remains None
                except Exception as e:
                    logo_info = None
                
                # Ensure content is not empty
                if not content.strip():
                    content = "DataSpark QR Code"  # Default content if empty
                
                # Generate QR code SVG with fallback logic
                try:
                    svg_content = generate_qr_svg(content, logo_info, qr_color, background_color, shape_type, use_white_bg, frame_type, frame_color)
                    if not svg_content:
                        # Fallback generation
                        svg_content = generate_qr_svg(content, None, '#000000', '#ffffff', 'square', True, 'none', '#000000')
                except Exception as e:
                    # Fallback generation
                    try:
                        svg_content = generate_qr_svg(content, None, '#000000', '#ffffff', 'square', True, 'none', '#000000')
                    except Exception as e2:
                        svg_content = None
                
                svg_content = generate_qr_svg(content, logo_info, qr_color, background_color, shape_type, use_white_bg, frame_type, frame_color)
                if svg_content:
                    response = HttpResponse(svg_content, content_type='image/svg+xml')
                    response['Content-Disposition'] = 'attachment; filename="dataspark_qrcode.svg"'
                    return response
        else:
            # Handle form submission
            form = QRGeneratorForm(request.POST, request.FILES)
            
            if form.is_valid():
                content = form.cleaned_data['content']
                logo_option = form.cleaned_data['logo_option']
                custom_logo = form.cleaned_data.get('custom_logo')
                qr_color = form.cleaned_data['qr_color']
                background_type = form.cleaned_data['background_type']
                shape_type = 'square'  # Fixed to square since shape option is removed
                frame_type = form.cleaned_data['frame_type']
                frame_color = form.cleaned_data['frame_color']
                
                # Convert background_type to background_color for processing
                background_color = '#ffffff' if background_type == 'white' else '#ffffff'
                use_white_bg = background_type == 'white'
                
                # Process logo based on selection - ensure QR generation always works
                logo_info = None
                try:
                    if logo_option == 'dataspark':
                        logo_info = process_logo_for_qr()
                        # If logo processing fails, continue without logo
                        if logo_info is None:
                            pass  # Continue without logo
                    elif logo_option == 'custom' and custom_logo:
                        logo_info = process_logo_for_qr(custom_logo)
                        # If custom logo processing fails, continue without logo
                        if logo_info is None:
                            pass  # Continue without logo
                    # If 'none' is selected, logo_info remains None
                except Exception as e:
                    logo_info = None
                
                # Ensure content is not empty
                if not content or not content.strip():
                    content = "DataSpark QR Code"  # Default content if empty
                
                # Generate QR code SVG with all options - this should ALWAYS work
                try:
                    svg_content = generate_qr_svg(content, logo_info, qr_color, background_color, shape_type, use_white_bg, frame_type, frame_color)
                    if not svg_content:
                        # Fallback: try generating with minimal options
                        svg_content = generate_qr_svg(content, None, '#000000', '#ffffff', 'square', True, 'none', '#000000')
                except Exception as e:
                    # Fallback: try generating with minimal options
                    try:
                        svg_content = generate_qr_svg(content, None, '#000000', '#ffffff', 'square', True, 'none', '#000000')
                    except Exception as e2:
                        svg_content = None
                
                download_ready = bool(svg_content)

    return render(request, 'qr_generator.html', context={
        'form': form,
        'svg_content': svg_content,
        'download_ready': download_ready,
        'qr_content': form.cleaned_data.get('content', '') if form.is_valid() else '',
        'logo_option': logo_option if form.is_valid() else 'dataspark',
        'qr_color': form.cleaned_data.get('qr_color', '#0066cc') if form.is_valid() else '#0066cc',
        'background_type': form.cleaned_data.get('background_type', 'transparent') if form.is_valid() else 'transparent',
        'shape_type': 'square',  # Fixed to square since shape option is removed
        'frame_type': form.cleaned_data.get('frame_type', 'none') if form.is_valid() else 'none',
        'frame_color': form.cleaned_data.get('frame_color', '#000000') if form.is_valid() else '#000000',
        'logo_info': logo_info
    })


@login_required
@user_passes_test(is_global_admin)
@csrf_protect  
def admin_overview(request):  
    restart = request.POST.get("restart") or request.GET.get("restart")
    if restart == 'true':
        if request.user.is_authenticated:
            logout(request)
        request.session.flush()
        os.system("cd .. && ./update_and_launch.sh")

    rate = os.getenv('RESOURCES_REFRESH', default=5000)

    last_launched = ""
    try:
        with open('last_launched.txt', 'r') as f:
            last_launched = f.read().strip()
    except FileNotFoundError:
        # If the file doesn't exist, create it with the current timestamp
        with open('last_launched.txt', 'w') as f:
            last_launched = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(last_launched)

    return render(request, 'admin_overview.html', {
        'refresh_rate': rate,
        'commit': os.popen('git log -1 --pretty=%B').read().strip(),
        'commit_hash': os.popen('git log -1 --pretty=%H').read().strip(),
        'last_launched': last_launched,
        'wdir': os.getcwd(),
        'logged_in_users': views_user.get_logged_in_users_count(),  # Add initial logged-in users count
        'session_info': views_user.get_session_details(),  # Add initial session details
        'resource_log_size': views_user.get_resource_log_file_size(),  # Add resource log file size
        'audit_log_count': views_user.get_audit_log_count(),  # Add audit log count
        'recent_audit_logs': views_user.get_recent_audit_logs(),  # Add recent audit logs
        #'users': user_data,
        #"fullness_percentage": int(round(fullness_percentage, 0)),
        #"total_gb": total_gb,
        #"used_gb": used_gb,
        #"free_gb": free_gb,
        #"ram_total": ram_total,
        #"ram_used": ram_used,
        #"ram_free": ram_free,
        #"ram_percentage": int(round(ram_percentage, 0)),
        #"cpu_percentage": int(round(cpu_percentage, 0)),
    })
