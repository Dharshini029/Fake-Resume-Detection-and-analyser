import os
import json
import uuid
import csv
import io
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
)
from werkzeug.utils import secure_filename

from config import Config
from core.database import (
    init_db, insert_resume, get_resume_by_id, list_resumes,
    update_resume_status, delete_resume, get_dashboard_stats,
    save_jd_evaluation, get_jd_evaluations_for_resume
)
from core.parser import parse_resume, extract_candidate_name, extract_contact_info, extract_skills, extract_education, extract_experience, extract_projects_and_certifications
from core.rule_engine import RuleEngine
from core.ml_engine import MLEngine
from core.hybrid_analyzer import HybridAnalyzer
from core.ai_explainer import AIExplainer
from core.jd_matcher import JDMatcher, SAMPLE_JOB_DESCRIPTIONS
from core.report_generator import generate_pdf_report

app = Flask(__name__)
app.config.from_object(Config)

# Ensure required directories exist
Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
Config.DEMO_FOLDER.mkdir(parents=True, exist_ok=True)
Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Initialize Database and Engines
init_db()
rule_engine = RuleEngine()
ml_engine = MLEngine()
hybrid_analyzer = HybridAnalyzer()
ai_explainer = AIExplainer()
jd_matcher = JDMatcher()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def process_resume_file(file_path, original_filename):
    """Full analysis pipeline for an uploaded or demo resume file"""
    parsed = parse_resume(file_path)
    rule_results = rule_engine.evaluate(parsed)
    ml_results = ml_engine.analyze(parsed['raw_text'])
    hybrid_results = hybrid_analyzer.compute(rule_results, ml_results)
    ai_results = ai_explainer.generate_explanation_and_questions(
        parsed, rule_results, ml_results, hybrid_results
    )
    
    file_type = Path(file_path).suffix.lower().replace('.', '')
    stored_filename = Path(file_path).name
    
    record = {
        'filename': stored_filename,
        'original_filename': original_filename,
        'file_path': str(file_path),
        'file_type': file_type,
        'candidate_name': parsed['candidate_name'],
        'candidate_email': parsed['candidate_email'],
        'candidate_phone': parsed['candidate_phone'],
        'candidate_location': parsed['candidate_location'],
        'linkedin': parsed['linkedin'],
        'github': parsed['github'],
        'raw_text': parsed['raw_text'],
        'extracted_data': parsed['extracted_data'],
        'rule_flags': rule_results['flags'],
        'rule_score': rule_results['rule_score'],
        'ml_score': ml_results['ml_score'],
        'ml_details': ml_results,
        'hybrid_score': hybrid_results['hybrid_score'],
        'credibility_score': hybrid_results['credibility_score'],
        'risk_level': hybrid_results['risk_level'],
        'ai_summary': ai_results['ai_summary'],
        'ai_verification_questions': ai_results['ai_verification_questions'],
        'review_status': 'Pending Review',
        'recruiter_notes': ''
    }
    
    resume_id = insert_resume(record)
    return resume_id, record

def process_resume_text(text, title="Pasted Resume Text"):
    """Pipeline for raw pasted resume text"""
    if not text or len(text.strip()) < 50:
        raise ValueError("Resume text is too short to analyze (minimum 50 characters required).")
        
    candidate_name = extract_candidate_name(text)
    contact_info = extract_contact_info(text)
    skills_data = extract_skills(text)
    education_data = extract_education(text)
    experience_data = extract_experience(text)
    extra_data = extract_projects_and_certifications(text)
    
    parsed = {
        'candidate_name': candidate_name,
        'candidate_email': contact_info['email'],
        'candidate_phone': contact_info['phone'],
        'candidate_location': contact_info['location'],
        'linkedin': contact_info['linkedin'],
        'github': contact_info['github'],
        'raw_text': text,
        'extracted_data': {
            'skills': skills_data,
            'education': education_data,
            'experience': experience_data,
            'projects': extra_data['projects'],
            'certifications': extra_data['certifications'],
            'word_count': len(text.split()),
            'char_count': len(text)
        }
    }
    
    # Save as text file in uploads
    filename = f"pasted_{uuid.uuid4().hex[:8]}.txt"
    file_path = Config.UPLOAD_FOLDER / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
        
    rule_results = rule_engine.evaluate(parsed)
    ml_results = ml_engine.analyze(parsed['raw_text'])
    hybrid_results = hybrid_analyzer.compute(rule_results, ml_results)
    ai_results = ai_explainer.generate_explanation_and_questions(
        parsed, rule_results, ml_results, hybrid_results
    )
    
    record = {
        'filename': filename,
        'original_filename': title,
        'file_path': str(file_path),
        'file_type': 'txt',
        'candidate_name': parsed['candidate_name'],
        'candidate_email': parsed['candidate_email'],
        'candidate_phone': parsed['candidate_phone'],
        'candidate_location': parsed['candidate_location'],
        'linkedin': parsed['linkedin'],
        'github': parsed['github'],
        'raw_text': parsed['raw_text'],
        'extracted_data': parsed['extracted_data'],
        'rule_flags': rule_results['flags'],
        'rule_score': rule_results['rule_score'],
        'ml_score': ml_results['ml_score'],
        'ml_details': ml_results,
        'hybrid_score': hybrid_results['hybrid_score'],
        'credibility_score': hybrid_results['credibility_score'],
        'risk_level': hybrid_results['risk_level'],
        'ai_summary': ai_results['ai_summary'],
        'ai_verification_questions': ai_results['ai_verification_questions'],
        'review_status': 'Pending Review',
        'recruiter_notes': ''
    }
    
    resume_id = insert_resume(record)
    return resume_id, record

# ==================== ROUTES ====================

@app.route('/')
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if request.method == 'GET':
        return render_template('scan.html')
        
    # POST handling
    # 1. Text Paste Mode
    if request.form.get('paste_text'):
        text = request.form.get('paste_text', '').strip()
        title = request.form.get('paste_title', '').strip() or 'Direct Pasted Resume'
        try:
            resume_id, _ = process_resume_text(text, title)
            flash('Resume text analyzed successfully!', 'success')
            return redirect(url_for('resume_detail', resume_id=resume_id))
        except Exception as e:
            flash(f'Analysis error: {str(e)}', 'danger')
            return redirect(url_for('scan'))
            
    # 2. File Uploads (Single or Batch)
    files = request.files.getlist('resume_files')
    if not files or files[0].filename == '':
        flash('Please select at least one PDF or DOCX resume to upload.', 'warning')
        return redirect(url_for('scan'))
        
    processed_ids = []
    errors = []
    
    for f in files:
        if f and allowed_file(f.filename):
            orig_name = secure_filename(f.filename)
            ext = orig_name.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex[:10]}_{orig_name}"
            save_path = Config.UPLOAD_FOLDER / unique_name
            f.save(save_path)
            
            try:
                res_id, _ = process_resume_file(save_path, orig_name)
                processed_ids.append(res_id)
            except Exception as e:
                errors.append(f"Error processing {orig_name}: {str(e)}")
        else:
            errors.append(f"Unsupported file format: {f.filename}. Only PDF and DOCX are accepted.")
            
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': len(processed_ids) > 0,
            'processed_ids': processed_ids,
            'count': len(processed_ids),
            'errors': errors,
            'redirect_url': url_for('resume_detail', resume_id=processed_ids[0]) if len(processed_ids) == 1 else url_for('history')
        })
        
    if errors:
        for err in errors:
            flash(err, 'danger')
            
    if len(processed_ids) == 1:
        flash('Resume successfully uploaded and evaluated!', 'success')
        return redirect(url_for('resume_detail', resume_id=processed_ids[0]))
    elif len(processed_ids) > 1:
        flash(f'Batch upload completed: {len(processed_ids)} resumes successfully evaluated!', 'success')
        return redirect(url_for('history'))
        
    return redirect(url_for('scan'))

@app.route('/api/demo/<demo_key>', methods=['POST', 'GET'])
def run_demo(demo_key):
    """1-Click Try Demo endpoint that analyzes a pre-generated sample resume"""
    demo_map = {
        'alex': ('alex_morgan_genuine_fullstack.pdf', 'Alex Morgan (Genuine Full-Stack Engineer)'),
        'david': ('david_chen_date_anomalies.pdf', 'David Chen (Severe Date Inconsistencies)'),
        'sarah': ('sarah_connor_buzzword_stuffed.docx', 'Sarah Connor (Buzzword Stuffing & Duplicates)'),
        'jordan': ('jordan_taylor_junior_inflated.pdf', 'Jordan Taylor (Junior Claiming CTO)')
    }
    
    if demo_key not in demo_map:
        flash('Invalid demo resume selection.', 'danger')
        return redirect(url_for('scan'))
        
    filename, display_name = demo_map[demo_key]
    demo_path = Config.DEMO_FOLDER / filename
    
    if not demo_path.exists():
        # Regenerate demo files if missing
        from demo_resumes.create_demo_files import generate_all_demos
        generate_all_demos()
        
    try:
        res_id, _ = process_resume_file(demo_path, display_name)
        flash(f'Demo resume "{display_name}" analyzed successfully!', 'success')
        return redirect(url_for('resume_detail', resume_id=res_id))
    except Exception as e:
        flash(f'Error analyzing demo resume: {str(e)}', 'danger')
        return redirect(url_for('scan'))

@app.route('/resume/<int:resume_id>')
def resume_detail(resume_id):
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('Resume record not found.', 'warning')
        return redirect(url_for('history'))
        
    # Get previous JD evaluations for this candidate
    jd_history = get_jd_evaluations_for_resume(resume_id)
    return render_template(
        'analysis_result.html',
        resume=resume,
        jd_history=jd_history,
        sample_jds=SAMPLE_JOB_DESCRIPTIONS
    )

@app.route('/resume/<int:resume_id>/status', methods=['POST'])
def update_status(resume_id):
    new_status = request.form.get('review_status')
    notes = request.form.get('recruiter_notes')
    if new_status:
        update_resume_status(resume_id, new_status, notes)
        flash('Recruiter review status and notes updated.', 'success')
    return redirect(url_for('resume_detail', resume_id=resume_id))

@app.route('/resume/<int:resume_id>/pdf')
def download_pdf(resume_id):
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('Resume record not found.', 'warning')
        return redirect(url_for('history'))
        
    pdf_bytes = generate_pdf_report(resume)
    safe_name = secure_filename(resume['candidate_name']).replace(' ', '_') or f"candidate_{resume_id}"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Audit_Report_{safe_name}.pdf"
    )

@app.route('/resume/<int:resume_id>/delete', methods=['POST'])
def delete_resume_route(resume_id):
    resume = get_resume_by_id(resume_id)
    if resume:
        # Delete file from disk if in uploads
        file_path = Path(resume['file_path'])
        if file_path.exists() and 'uploads' in str(file_path):
            try:
                file_path.unlink()
            except Exception:
                pass
        delete_resume(resume_id)
        flash('Resume record deleted successfully.', 'info')
    return redirect(url_for('history'))

@app.route('/history')
def history():
    search = request.args.get('search', '').strip()
    risk_level = request.args.get('risk_level', 'All')
    review_status = request.args.get('review_status', 'All')
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'DESC')
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    resumes, total_count = list_resumes(
        search=search if search else None,
        risk_level=risk_level,
        review_status=review_status,
        sort_by=sort_by,
        order=order,
        limit=per_page,
        offset=offset
    )
    
    total_pages = (total_count + per_page - 1) // per_page
    return render_template(
        'history.html',
        resumes=resumes,
        total_count=total_count,
        search=search,
        risk_level=risk_level,
        review_status=review_status,
        sort_by=sort_by,
        order=order,
        page=page,
        total_pages=total_pages
    )

@app.route('/export/csv')
def export_csv():
    search = request.args.get('search', '').strip()
    risk_level = request.args.get('risk_level', 'All')
    review_status = request.args.get('review_status', 'All')
    
    resumes, _ = list_resumes(
        search=search if search else None,
        risk_level=risk_level,
        review_status=review_status,
        limit=1000
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Candidate Name', 'Original File', 'Risk Level', 'Risk Score (0-100)',
        'Credibility Index (%)', 'Rule Score', 'ML Score (%)', 'Total Flags',
        'Review Status', 'Recruiter Notes', 'Created At'
    ])
    
    for r in resumes:
        writer.writerow([
            r['id'],
            r['candidate_name'],
            r['original_filename'],
            r['risk_level'],
            r['hybrid_score'],
            r['credibility_score'],
            r['rule_score'],
            r['ml_score'],
            len(r.get('rule_flags', [])),
            r['review_status'],
            r.get('recruiter_notes', ''),
            r['created_at']
        ])
        
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=Resume_Credibility_Export.csv'}
    )

@app.route('/jd-matching', methods=['GET', 'POST'])
def jd_matching():
    all_resumes, _ = list_resumes(limit=100)
    selected_resume_id = request.args.get('resume_id') or (all_resumes[0]['id'] if all_resumes else None)
    
    evaluation_result = None
    selected_resume = None
    jd_text = ""
    job_title = "Custom Position"
    
    if selected_resume_id:
        selected_resume = get_resume_by_id(int(selected_resume_id))
        
    if request.method == 'POST':
        resume_id = int(request.form.get('resume_id'))
        selected_resume = get_resume_by_id(resume_id)
        job_title = request.form.get('job_title', 'Job Evaluation')
        jd_text = request.form.get('jd_text', '').strip()
        
        if selected_resume and jd_text:
            skills = selected_resume.get('extracted_data', {}).get('skills', {})
            evaluation_result = jd_matcher.evaluate_match(
                selected_resume['raw_text'], skills, jd_text
            )
            # Save to database
            save_jd_evaluation(
                resume_id=resume_id,
                job_title=job_title,
                jd_text=jd_text,
                match_score=evaluation_result['match_score'],
                matched_skills=evaluation_result['matched_skills'],
                missing_skills=evaluation_result['missing_skills'],
                recommendation=evaluation_result['recommendation']
            )
            flash('Job description evaluation completed!', 'success')
            
    return render_template(
        'jd_matching.html',
        resumes=all_resumes,
        selected_resume=selected_resume,
        evaluation=evaluation_result,
        sample_jds=SAMPLE_JOB_DESCRIPTIONS,
        current_title=job_title,
        current_jd=jd_text
    )

@app.route('/api/jd-evaluate', methods=['POST'])
def api_jd_evaluate():
    """AJAX API for interactive JD matching on candidate detail page"""
    data = request.get_json() or {}
    resume_id = data.get('resume_id')
    jd_text = data.get('jd_text', '')
    job_title = data.get('job_title', 'Evaluated Role')
    
    if not resume_id or not jd_text:
        return jsonify({'error': 'Missing resume_id or jd_text'}), 400
        
    resume = get_resume_by_id(int(resume_id))
    if not resume:
        return jsonify({'error': 'Resume not found'}), 404
        
    skills = resume.get('extracted_data', {}).get('skills', {})
    result = jd_matcher.evaluate_match(resume['raw_text'], skills, jd_text)
    
    save_jd_evaluation(
        resume_id=resume['id'],
        job_title=job_title,
        jd_text=jd_text,
        match_score=result['match_score'],
        matched_skills=result['matched_skills'],
        missing_skills=result['missing_skills'],
        recommendation=result['recommendation']
    )
    
    return jsonify(result)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    print("=" * 65)
    print("AI-POWERED FAKE RESUME ANALYSER & DETECTION SYSTEM")
    print(f"Local Server: http://{Config.HOST}:{Config.PORT}")
    print("=" * 65)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
