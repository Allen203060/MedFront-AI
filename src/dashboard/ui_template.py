"""
Clinical Medicine UI/UX Template for MedFront / AuraCare Healthcare Voice AI.
Implements a state-of-the-art Clinical HealthTech Portal with:
- Primary Medical Light Theme default with optional Dark Mode toggle
- Ambient AI Clinical Scribe with bug-free speech recognition and GPT-4o SOAP generation
- One-click "Open in Scribe" flow with auto-selection and smooth scroll
- Dedicated interactive AI Voice Receptionist Console
- Full Patients Directory with live search and Active Patient status
- Multi-specialty clinician roster (Cardiology, GP, Dermatology, Orthopedics, Pediatrics)
- "Add New Doctor" onboarding flow
- Clean, structured, uncluttered presentation
"""


def render_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraCare Health Portal | Hospital Clinical & Voice AI</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        /* ==================================================================== */
        /* CSS DESIGN SYSTEM - PRIMARY LIGHT THEME (DEFAULT) & SLEEK DARK THEME */
        /* ==================================================================== */
        :root {
            /* Primary Medical Light Theme Defaults */
            --bg-base: #f8fafc;
            --bg-surface: #ffffff;
            --bg-card: #ffffff;
            --bg-card-subtle: #f1f5f9;
            --bg-card-hover: #f8fafc;
            --border-subtle: #e2e8f0;
            --border-strong: #cbd5e1;
            --border-glow: rgba(13, 148, 136, 0.4);
            
            --shadow-card: 0 2px 8px rgba(15, 23, 42, 0.05), 0 1px 2px rgba(15, 23, 42, 0.06);
            --shadow-elevated: 0 12px 28px -4px rgba(15, 23, 42, 0.08), 0 4px 10px -2px rgba(15, 23, 42, 0.04);
            
            --teal-500: #0d9488;
            --teal-600: #0f766e;
            --teal-50: #f0fdfa;
            --teal-100: #ccfbf1;
            
            --cyan-500: #0284c7;
            --cyan-50: #f0f9ff;
            
            --emerald-500: #059669;
            --emerald-50: #ecfdf5;
            
            --blue-500: #2563eb;
            --amber-500: #d97706;
            --amber-50: #fffbeb;
            --rose-500: #e11d48;
            --rose-50: #fff1f2;
            
            --text-main: #0f172a;
            --text-muted: #475569;
            --text-sub: #64748b;
            --text-inverse: #ffffff;
            
            --header-bg: rgba(255, 255, 255, 0.96);
            --header-border: #e2e8f0;
            --input-bg: #ffffff;
            --input-border: #cbd5e1;
            --table-header-bg: #f8fafc;
            --table-row-hover: #f8fafc;
            --bubble-user-bg: #e0f2fe;
            --bubble-user-text: #0369a1;
            --bubble-agent-bg: #f0fdf4;
            --bubble-agent-text: #166534;
        }

        [data-theme="dark"] {
            /* Dark Theme Overrides */
            --bg-base: #070d18;
            --bg-surface: #0d1527;
            --bg-card: rgba(16, 26, 46, 0.92);
            --bg-card-subtle: rgba(22, 36, 64, 0.75);
            --bg-card-hover: rgba(22, 36, 64, 0.95);
            --border-subtle: rgba(13, 148, 136, 0.22);
            --border-strong: rgba(255, 255, 255, 0.15);
            --border-glow: rgba(20, 184, 166, 0.45);
            
            --shadow-card: 0 4px 20px rgba(0, 0, 0, 0.4);
            --shadow-elevated: 0 14px 35px rgba(0, 0, 0, 0.6);
            
            --teal-500: #14b8a6;
            --teal-600: #0d9488;
            --teal-50: rgba(13, 148, 136, 0.15);
            --teal-100: rgba(13, 148, 136, 0.25);
            
            --cyan-500: #06b6d4;
            --cyan-50: rgba(6, 182, 212, 0.15);
            
            --emerald-500: #10b981;
            --emerald-50: rgba(16, 185, 129, 0.15);
            
            --blue-500: #3b82f6;
            --amber-500: #f59e0b;
            --amber-50: rgba(245, 158, 11, 0.15);
            --rose-500: #f43f5e;
            --rose-50: rgba(244, 63, 94, 0.15);
            
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-sub: #64748b;
            --text-inverse: #0f172a;
            
            --header-bg: rgba(10, 18, 32, 0.94);
            --header-border: rgba(13, 148, 136, 0.22);
            --input-bg: #0b1329;
            --input-border: #1e293b;
            --table-header-bg: rgba(15, 23, 42, 0.7);
            --table-row-hover: rgba(13, 148, 136, 0.08);
            --bubble-user-bg: #1e293b;
            --bubble-user-text: #38bdf8;
            --bubble-agent-bg: #16243b;
            --bubble-agent-text: #e2e8f0;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-base);
            background-image: 
                radial-gradient(at 0% 0%, rgba(13, 148, 136, 0.07) 0px, transparent 40%),
                radial-gradient(at 100% 100%, rgba(2, 132, 199, 0.05) 0px, transparent 40%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            transition: background 0.25s ease, color 0.25s ease;
        }

        /* Top Header - Spacious 3-Column Layout with No Overlap */
        header {
            background: var(--header-bg);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--header-border);
            position: sticky;
            top: 0;
            z-index: 100;
            padding: 0.85rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            box-shadow: 0 1px 4px rgba(0,0,0,0.03);
        }

        .brand-section {
            display: flex;
            align-items: center;
            gap: 0.9rem;
            min-width: 280px;
        }
        .brand-logo {
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, #0d9488, #0284c7);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
            flex-shrink: 0;
        }
        .brand-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-main);
            line-height: 1.2;
        }
        .brand-subtitle {
            font-size: 0.74rem;
            color: var(--text-muted);
            letter-spacing: 0.02em;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        /* Top Navigation Tabs Bar */
        .tabs-nav {
            display: flex;
            align-items: center;
            background: var(--bg-card-subtle);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 0.25rem;
            gap: 0.35rem;
        }
        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.55rem 1.05rem;
            border-radius: 9px;
            font-size: 0.86rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.45rem;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .tab-btn:hover {
            color: var(--text-main);
            background: rgba(13, 148, 136, 0.08);
        }
        .tab-btn.active {
            background: var(--bg-surface);
            color: var(--teal-500);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--border-subtle);
        }

        /* Header Right Controls */
        .header-actions {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            min-width: 260px;
            justify-content: flex-end;
        }
        .theme-toggle-btn {
            background: var(--bg-card-subtle);
            border: 1px solid var(--border-subtle);
            color: var(--text-main);
            padding: 0.5rem 0.85rem;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .theme-toggle-btn:hover {
            border-color: var(--teal-500);
            background: var(--teal-50);
        }

        .pulse-badge {
            display: flex;
            align-items: center;
            gap: 0.45rem;
            background: var(--teal-50);
            border: 1px solid rgba(13, 148, 136, 0.3);
            color: var(--teal-600);
            font-size: 0.72rem;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            white-space: nowrap;
        }
        .pulse-dot {
            width: 7px;
            height: 7px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
            animation: livePulse 1.8s infinite;
        }
        @keyframes livePulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.3); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }

        /* Main Container */
        main {
            flex: 1;
            padding: 1.5rem 2rem 3rem 2rem;
            max-width: 1680px;
            width: 100%;
            margin: 0 auto;
        }

        /* Views */
        .portal-view { display: none; }
        .portal-view.active-view { display: block; animation: fadeIn 0.25s ease-out; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Cards and Panels */
        .glass-panel {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 1.5rem;
            box-shadow: var(--shadow-card);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .glass-panel:hover {
            box-shadow: var(--shadow-elevated);
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-subtle);
        }
        .panel-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-main);
        }

        /* Buttons */
        .btn-primary {
            background: linear-gradient(135deg, var(--teal-600) 0%, var(--teal-500) 100%);
            color: #ffffff;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            box-shadow: 0 2px 8px rgba(13, 148, 136, 0.3);
            transition: all 0.2s;
        }
        .btn-primary:hover {
            filter: brightness(1.08);
            transform: translateY(-1px);
        }
        .btn-secondary {
            background: var(--bg-card-subtle);
            border: 1px solid var(--border-strong);
            color: var(--text-main);
            padding: 0.55rem 1rem;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.2s;
        }
        .btn-secondary:hover {
            background: var(--teal-50);
            border-color: var(--teal-500);
            color: var(--teal-600);
        }
        .btn-danger {
            background: var(--rose-50);
            border: 1px solid var(--rose-500);
            color: var(--rose-500);
            padding: 0.35rem 0.75rem;
            border-radius: 6px;
            font-size: 0.76rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-danger:hover {
            background: var(--rose-500);
            color: #ffffff;
        }

        /* Clinician Selector Banner */
        .doctor-selector-bar {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            box-shadow: var(--shadow-card);
        }
        .doctor-profile {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .doctor-avatar {
            width: 52px;
            height: 52px;
            background: var(--teal-50);
            border: 2px solid var(--teal-500);
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
        }
        .doctor-name {
            font-family: 'Outfit', sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-main);
        }
        .doctor-meta {
            font-size: 0.8rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-top: 0.15rem;
        }
        .select-doctor-dropdown {
            background: var(--input-bg);
            border: 1px solid var(--border-strong);
            color: var(--text-main);
            padding: 0.65rem 1.1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            outline: none;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .select-doctor-dropdown:focus {
            border-color: var(--teal-500);
        }

        /* Doctor Layout Grid (Left: Queue, Right: Scribe Studio) */
        .doctor-layout-grid {
            display: grid;
            grid-template-columns: 420px 1fr;
            gap: 1.5rem;
        }
        @media (max-width: 1100px) {
            .doctor-layout-grid { grid-template-columns: 1fr; }
        }

        /* Patient Appointments Queue Cards */
        .appt-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 0.85rem;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .appt-card:hover {
            border-color: var(--teal-500);
            transform: translateY(-2px);
            box-shadow: var(--shadow-card);
        }
        .appt-card.active-selected {
            border: 2px solid var(--teal-500);
            background: var(--teal-50);
        }
        .appt-card-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.4rem;
        }
        .appt-time-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--teal-600);
            background: var(--teal-100);
            padding: 0.2rem 0.5rem;
            border-radius: 5px;
        }
        .patient-card-name {
            font-weight: 700;
            font-size: 0.95rem;
            color: var(--text-main);
        }
        .patient-card-mrn {
            font-size: 0.76rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }
        .appt-reason-text {
            font-size: 0.8rem;
            color: var(--text-sub);
            margin: 0.4rem 0 0.6rem 0;
            font-style: italic;
        }
        .appt-actions-row {
            display: flex;
            gap: 0.5rem;
        }

        /* Ambient AI Clinical Scribe Studio */
        .scribe-studio {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 1.5rem;
            box-shadow: var(--shadow-card);
            transition: all 0.3s ease;
        }
        .scribe-studio-highlight {
            animation: pulseGlow 2s ease-in-out 2;
        }
        @keyframes pulseGlow {
            0% { border-color: var(--teal-500); box-shadow: 0 0 0 0 rgba(13, 148, 136, 0.4); }
            50% { border-color: var(--teal-500); box-shadow: 0 0 20px 4px rgba(13, 148, 136, 0.3); }
            100% { border-color: var(--border-subtle); box-shadow: var(--shadow-card); }
        }

        .scribe-banner {
            background: linear-gradient(135deg, rgba(13, 148, 136, 0.1) 0%, rgba(2, 132, 199, 0.08) 100%);
            border: 1px solid rgba(13, 148, 136, 0.25);
            border-radius: 10px;
            padding: 1rem 1.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
        }
        .scribe-patient-info {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }
        .scribe-patient-name {
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-main);
        }
        .scribe-patient-mrn {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: var(--teal-600);
        }

        /* Audio Recording Bar */
        .audio-recorder-bar {
            background: var(--bg-surface);
            border: 1px dashed var(--border-strong);
            border-radius: 10px;
            padding: 1.1rem;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .btn-record-mic {
            background: var(--teal-50);
            border: 1px solid var(--teal-500);
            color: var(--teal-600);
            padding: 0.65rem 1.25rem;
            border-radius: 30px;
            font-size: 0.88rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.2s;
        }
        .btn-record-mic:hover {
            background: var(--teal-500);
            color: #ffffff;
        }
        .btn-record-mic.recording {
            background: var(--rose-500);
            border-color: var(--rose-500);
            color: #ffffff;
            animation: livePulse 1.2s infinite;
        }

        .raw-transcript-box {
            width: 100%;
            height: 110px;
            background: var(--input-bg);
            border: 1px solid var(--border-strong);
            border-radius: 8px;
            padding: 0.8rem;
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 0.88rem;
            line-height: 1.5;
            resize: vertical;
            outline: none;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        }
        .raw-transcript-box:focus {
            border-color: var(--teal-500);
            box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.15);
        }

        /* SOAP Note 4-Quadrant Form */
        .soap-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.25rem;
        }
        @media (max-width: 800px) {
            .soap-grid { grid-template-columns: 1fr; }
        }
        .soap-block {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .soap-label {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--teal-600);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .soap-textarea {
            width: 100%;
            height: 90px;
            background: var(--input-bg);
            border: 1px solid var(--border-strong);
            border-radius: 6px;
            padding: 0.6rem;
            color: var(--text-main);
            font-size: 0.85rem;
            line-height: 1.45;
            resize: vertical;
            outline: none;
        }
        .soap-textarea:focus {
            border-color: var(--teal-500);
        }

        /* Confirmation Status Ribbon */
        .doctor-approval-gate {
            background: var(--teal-50);
            border: 1px solid var(--teal-500);
            border-radius: 10px;
            padding: 1rem 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }

        /* Tables */
        .custom-table-container {
            width: 100%;
            overflow-x: auto;
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            background: var(--bg-surface);
            box-shadow: var(--shadow-card);
        }
        table.med-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            text-align: left;
        }
        table.med-table th {
            background: var(--table-header-bg);
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.72rem;
            letter-spacing: 0.05em;
            padding: 0.85rem 1rem;
            border-bottom: 1px solid var(--border-subtle);
        }
        table.med-table td {
            padding: 0.85rem 1rem;
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text-main);
            vertical-align: middle;
        }
        table.med-table tr:hover td {
            background: var(--table-row-hover);
        }

        /* Status Badges */
        .badge-confirmed {
            background: var(--emerald-50);
            color: var(--emerald-500);
            border: 1px solid rgba(5, 150, 105, 0.3);
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 700;
            display: inline-block;
        }
        .badge-cancelled {
            background: var(--rose-50);
            color: var(--rose-500);
            border: 1px solid rgba(225, 29, 72, 0.3);
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 700;
            display: inline-block;
        }
        .badge-active-patient {
            background: var(--emerald-50);
            color: var(--emerald-500);
            border: 1px solid rgba(5, 150, 105, 0.3);
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin-bottom: 1.5rem;
        }
        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: var(--shadow-card);
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: var(--teal-50);
            color: var(--teal-500);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        .stat-val {
            font-family: 'Outfit', sans-serif;
            font-size: 1.65rem;
            font-weight: 800;
            color: var(--text-main);
        }
        .stat-title {
            font-size: 0.78rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        /* Voice Agent Call Console View */
        .voice-console-grid {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 1.5rem;
        }
        @media (max-width: 960px) {
            .voice-console-grid { grid-template-columns: 1fr; }
        }
        .transcript-feed {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            height: 440px;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }
        .bubble-msg {
            padding: 0.8rem 1rem;
            border-radius: 12px;
            font-size: 0.88rem;
            line-height: 1.5;
            max-width: 85%;
        }
        .bubble-user {
            background: var(--bubble-user-bg);
            color: var(--bubble-user-text);
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }
        .bubble-agent {
            background: var(--bubble-agent-bg);
            color: var(--bubble-agent-text);
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }
        .tool-badge-pill {
            background: #ede9fe;
            color: #6d28d9;
            border: 1px solid #ddd6fe;
            padding: 0.2rem 0.5rem;
            border-radius: 6px;
            font-size: 0.72rem;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            display: inline-block;
            margin-top: 0.3rem;
        }

        /* Modals */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(15, 23, 42, 0.65);
            backdrop-filter: blur(6px);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .modal-card {
            background: var(--bg-card);
            border: 1px solid var(--border-strong);
            border-radius: 16px;
            width: 100%;
            max-width: 680px;
            max-height: 88vh;
            overflow-y: auto;
            box-shadow: var(--shadow-elevated);
            animation: modalPop 0.25s ease-out;
        }
        @keyframes modalPop {
            from { transform: scale(0.95); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .modal-header {
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-body {
            padding: 1.5rem;
        }
        .close-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.5rem;
            cursor: pointer;
            line-height: 1;
        }
        .close-btn:hover { color: var(--rose-500); }

        /* Form Inputs */
        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }
        @media (max-width: 600px) {
            .form-grid { grid-template-columns: 1fr; }
        }
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }
        .form-group label {
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-muted);
        }
        .form-control {
            background: var(--input-bg);
            border: 1px solid var(--border-strong);
            border-radius: 8px;
            padding: 0.65rem 0.85rem;
            color: var(--text-main);
            font-size: 0.88rem;
            outline: none;
            width: 100%;
        }
        .form-control:focus {
            border-color: var(--teal-500);
            box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.15);
        }

        /* Search input bar */
        .search-bar-wrap {
            position: relative;
            width: 100%;
            max-width: 480px;
        }
        .search-bar-wrap input {
            width: 100%;
            padding: 0.65rem 1rem 0.65rem 2.4rem;
            border-radius: 8px;
            border: 1px solid var(--border-strong);
            background: var(--input-bg);
            color: var(--text-main);
            font-size: 0.86rem;
            outline: none;
        }
        .search-bar-wrap input:focus {
            border-color: var(--teal-500);
        }
        .search-bar-icon {
            position: absolute;
            left: 0.85rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 0.9rem;
        }
    </style>
</head>
<body>

    <!-- ==================================================================== -->
    <!-- TOP CLINICAL NAVIGATION HEADER                                        -->
    <!-- ==================================================================== -->
    <header>
        <div class="brand-section">
            <div class="brand-logo">🏥</div>
            <div>
                <div class="brand-title">AuraCare Health Portal</div>
                <div class="brand-subtitle">
                    <span>Hospital Dashboard & Receptionist Inspector</span>
                </div>
            </div>
        </div>

        <!-- Top Role Navigation Tabs -->
        <nav class="tabs-nav">
            <button id="tabBtnDoctor" class="tab-btn active" onclick="switchPortalTab('doctor')">
                <span>🩺 Doctor Portal</span>
            </button>
            <button id="tabBtnReceptionist" class="tab-btn" onclick="switchPortalTab('receptionist')">
                <span>📋 Receptionist Portal</span>
            </button>
            <button id="tabBtnPatients" class="tab-btn" onclick="switchPortalTab('patients')">
                <span>👥 Patients Directory</span>
            </button>
            <button id="tabBtnVoice" class="tab-btn" onclick="switchPortalTab('voice')">
                <span>🎙️ AI Receptionist</span>
            </button>
        </nav>

        <!-- Right Header Action Tools -->
        <div class="header-actions">
            <button class="btn-secondary" onclick="openAddDoctorModal()" title="Onboard a new clinician to the clinic roster">
                <span>➕ Add Doctor</span>
            </button>
            <button class="theme-toggle-btn" onclick="toggleTheme()" id="themeToggleBtn" title="Toggle Light / Dark theme">
                <span id="themeToggleIcon">🌙</span>
                <span id="themeToggleText">Dark Mode</span>
            </button>
            <div class="pulse-badge">
                <span class="pulse-dot"></span>
                <span id="headerCloudStatus">AZURE CLOUD ACTIVE</span>
            </div>
        </div>
    </header>

    <main>

        <!-- ==================================================================== -->
        <!-- VIEW 1: DOCTOR PORTAL                                               -->
        <!-- ==================================================================== -->
        <div id="viewDoctorPortal" class="portal-view active-view">
            
            <!-- Clinician Selector & Profile Banner -->
            <div class="doctor-selector-bar">
                <div class="doctor-profile">
                    <div class="doctor-avatar" id="docAvatar">🫀</div>
                    <div>
                        <div class="doctor-name" id="docDisplayName">Dr. Ananya Rao</div>
                        <div class="doctor-meta">
                            <span id="docBadge" style="font-weight: 600; color: var(--teal-600);">Chief Cardiologist</span>
                            <span>•</span>
                            <span id="docDept">Department of Cardiovascular Sciences</span>
                            <span>•</span>
                            <span id="docQual" style="color: var(--text-muted);">MD (AIIMS), FACC</span>
                        </div>
                    </div>
                </div>

                <div style="display: flex; align-items: center; gap: 0.8rem;">
                    <label style="font-size: 0.82rem; color: var(--text-muted); font-weight: 700;">ACTIVE CLINICIAN:</label>
                    <select id="doctorSelectorDropdown" class="select-doctor-dropdown" onchange="onDoctorChanged()">
                        <!-- Populated dynamically from API -->
                    </select>
                </div>
            </div>

            <!-- Doctor Main Layout: Queue on Left, Ambient Scribe on Right -->
            <div class="doctor-layout-grid">
                
                <!-- Left Column: Doctor's Scheduled Appointments -->
                <div class="glass-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span>📅 Consultation Queue</span>
                            <span id="doctorApptCountBadge" class="appt-time-badge">0 Patients</span>
                        </div>
                        <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.3rem 0.6rem;" onclick="loadDoctorAppointments()">
                            🔄 Refresh
                        </button>
                    </div>

                    <div id="doctorAppointmentsContainer">
                        <div style="color: var(--text-muted); text-align: center; padding: 2rem;">Loading doctor schedule...</div>
                    </div>
                </div>

                <!-- Right Column: Ambient AI Clinical Scribe Studio -->
                <div class="scribe-studio" id="scribeStudio">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span>🎙️ Ambient AI Clinical Scribe Studio</span>
                            <span style="font-size: 0.72rem; background: var(--teal-50); color: var(--teal-600); border: 1px solid var(--teal-500); padding: 0.2rem 0.5rem; border-radius: 12px; font-weight: 700;">
                                GPT-4o SOAP + AZURE SEARCH
                            </span>
                        </div>
                        <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.3rem 0.6rem;" onclick="openPatientChart(document.getElementById('scribeTargetPatientId').innerText)">
                            📂 View Longitudinal Chart
                        </button>
                    </div>

                    <!-- Active Encounter Context Banner -->
                    <div class="scribe-banner">
                        <div class="scribe-patient-info">
                            <span style="font-size: 0.72rem; text-transform: uppercase; color: var(--teal-600); font-weight: 700;">Active Clinical Encounter:</span>
                            <span id="scribeTargetPatientName" class="scribe-patient-name">Select a patient from the queue</span>
                            <span class="scribe-patient-mrn">MRN: <span id="scribeTargetPatientId">None</span> • Date: <span id="scribeTargetDate">Today</span></span>
                        </div>
                        <button class="btn-secondary" style="font-size: 0.78rem;" onclick="loadSampleTranscript()">
                            📑 Load Clinical Dialogue
                        </button>
                    </div>

                    <!-- Audio Recording & Live Dictation -->
                    <div class="audio-recorder-bar">
                        <div style="display: flex; align-items: center; gap: 0.8rem;">
                            <button id="btnListenAmbient" class="btn-record-mic" onclick="toggleListening()">
                                <span>🎙️ Start Ambient Scribe (Mic)</span>
                            </button>
                            <span id="recordingTimer" style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: var(--rose-500); display: none; font-weight: 600;">
                                🔴 RECORDING LIVE
                            </span>
                        </div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">
                            Speech is transcribed in real-time with deduplication.
                        </div>
                    </div>

                    <!-- Live Consultation Transcript Box -->
                    <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em;">
                        Consultation Transcript / Dictation:
                    </div>
                    <textarea id="rawTranscriptInput" class="raw-transcript-box" placeholder="Speak into the microphone or type clinical notes here..."></textarea>

                    <div style="display: flex; justify-content: flex-end; margin-bottom: 1.25rem;">
                        <button id="btnGenerateSoap" class="btn-primary" onclick="generateSoapNote()">
                            <span>✨ Generate Structured SOAP Note (GPT-4o)</span>
                        </button>
                    </div>

                    <!-- Generated SOAP Note 4-Quadrant Form -->
                    <div class="soap-grid">
                        <div class="soap-block">
                            <div class="soap-label"><span>🗣️</span> Subjective (Symptom History)</div>
                            <textarea id="soapSubjective" class="soap-textarea" placeholder="Chief complaints, history of present illness, patient reported symptoms..."></textarea>
                        </div>
                        <div class="soap-block">
                            <div class="soap-label"><span>🩺</span> Objective (Clinical Vitals)</div>
                            <textarea id="soapObjective" class="soap-textarea" placeholder="Physical examination findings, vitals, lab reports, diagnostic results..."></textarea>
                        </div>
                        <div class="soap-block">
                            <div class="soap-label"><span>🔬</span> Assessment (Clinical Diagnosis)</div>
                            <textarea id="soapAssessment" class="soap-textarea" placeholder="Differential diagnosis, primary diagnostic formulation, ICD-10 assessment..."></textarea>
                        </div>
                        <div class="soap-block">
                            <div class="soap-label"><span>💊</span> Plan (Therapeutic Rx & Follow-Up)</div>
                            <textarea id="soapPlan" class="soap-textarea" placeholder="Prescription medications, diagnostic orders, lifestyle counseling, follow-up timeline..."></textarea>
                        </div>
                    </div>

                    <!-- Doctor Approval & Confirmation Gate -->
                    <div class="doctor-approval-gate">
                        <div>
                            <div style="font-weight: 700; font-size: 0.9rem; color: var(--teal-600);">
                                🛡️ Clinical Approval Gate (HIPAA Safe)
                            </div>
                            <div style="font-size: 0.78rem; color: var(--text-muted);">
                                Review and edit the AI-generated SOAP fields before signing and indexing into Azure AI Search.
                            </div>
                        </div>
                        <button id="btnConfirmNote" class="btn-primary" onclick="confirmAndSaveNote()">
                            <span>💾 Sign & Save Clinical Note to EHR</span>
                        </button>
                    </div>

                </div>
            </div>
        </div>


        <!-- ==================================================================== -->
        <!-- VIEW 2: RECEPTIONIST PORTAL                                          -->
        <!-- ==================================================================== -->
        <div id="viewReceptionistPortal" class="portal-view">
            
            <!-- High Level Metric Stats Cards -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">📅</div>
                    <div>
                        <div class="stat-val" id="statTotalAppointments">--</div>
                        <div class="stat-title">Confirmed Bookings</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">👨‍⚕️</div>
                    <div>
                        <div class="stat-val" id="statActiveDoctors">5</div>
                        <div class="stat-title">Active Clinicians</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">👥</div>
                    <div>
                        <div class="stat-val" id="statRegisteredPatients">--</div>
                        <div class="stat-title">Registered Patients</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🔍</div>
                    <div>
                        <div class="stat-val" id="statSearchIndexed">Active</div>
                        <div class="stat-title">Azure AI Search Index</div>
                    </div>
                </div>
            </div>

            <!-- Receptionist Quick Actions Bar -->
            <div class="doctor-selector-bar">
                <div>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 700; color: var(--text-main);">
                        Administrative Front-Desk Desk
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">
                        Manage appointment schedules, patient onboarding, and bookings
                    </div>
                </div>

                <div style="display: flex; gap: 0.65rem; flex-wrap: wrap;">
                    <button class="btn-primary" onclick="openNewPatientModal()">
                        <span>➕ Onboard New Patient</span>
                    </button>
                    <button class="btn-secondary" onclick="openDirectBookingModal()">
                        <span>📅 Book Direct Appointment</span>
                    </button>
                    <button class="btn-secondary" onclick="openAddDoctorModal()">
                        <span>👨‍⚕️ Add New Doctor</span>
                    </button>
                </div>
            </div>

            <!-- Master Appointments Registry Table -->
            <div class="glass-panel" style="margin-bottom: 1.5rem;">
                <div class="panel-header">
                    <div class="panel-title">
                        <span>📋 Master Appointment Bookings</span>
                        <span id="receptionistApptBadge" class="appt-time-badge">0 Total</span>
                    </div>

                    <div class="search-bar-wrap">
                        <span class="search-bar-icon">🔍</span>
                        <input id="searchAppointmentInput" type="text" placeholder="Search by Patient MRN, Name, Doctor, or Reason..." onkeyup="filterAppointmentsTable()">
                    </div>
                </div>

                <div class="custom-table-container">
                    <table class="med-table" id="masterAppointmentsTable">
                        <thead>
                            <tr>
                                <th>Ticket / ID</th>
                                <th>Patient Name</th>
                                <th>MRN</th>
                                <th>Doctor</th>
                                <th>Date & Time</th>
                                <th>Reason</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="masterAppointmentsTbody">
                            <tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading appointment registry...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Dispatched Appointment Notification Tickets (SMS) -->
            <div class="glass-panel" style="margin-top: 1.5rem;">
                <div class="panel-header">
                    <div class="panel-title">
                        <span>📨 Dispatched Appointment Confirmation Tickets (SMS)</span>
                        <span id="notificationTicketsCountBadge" class="appt-time-badge">0 Sent</span>
                    </div>
                    <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.3rem 0.6rem;" onclick="loadNotificationTickets()">
                        🔄 Refresh Tickets
                    </button>
                </div>

                <div class="custom-table-container">
                    <table class="med-table">
                        <thead>
                            <tr>
                                <th>Ticket ID</th>
                                <th>Patient Name</th>
                                <th>Recipient Phone</th>
                                <th>Clinician</th>
                                <th>Date & Time</th>
                                <th>Delivery Status</th>
                                <th>Confirmation Message</th>
                                <th>Dispatched At</th>
                            </tr>
                        </thead>
                        <tbody id="notificationTicketsTbody">
                            <tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading notification tickets...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Clinician Upcoming Availability Grid -->
            <div class="glass-panel">
                <div class="panel-header">
                    <div class="panel-title">
                        <span>🕒 Clinician Real-Time Availability (Next 3 Days)</span>
                    </div>
                    <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.3rem 0.6rem;" onclick="loadClinicianSchedules()">
                        🔄 Refresh Schedules
                    </button>
                </div>

                <div id="clinicianSchedulesGrid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem;">
                    <div style="color: var(--text-muted);">Loading clinician schedules...</div>
                </div>
            </div>

        </div>


        <!-- ==================================================================== -->
        <!-- VIEW 3: PATIENTS DIRECTORY (ALL REGISTERED PATIENTS)                -->
        <!-- ==================================================================== -->
        <div id="viewPatientsDirectory" class="portal-view">
            
            <div class="doctor-selector-bar">
                <div>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 700; color: var(--text-main);">
                        👥 Clinic Patients Directory
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">
                        All registered patients with longitudinal EHR medical charts
                    </div>
                </div>

                <div style="display: flex; gap: 0.8rem; align-items: center;">
                    <div class="search-bar-wrap" style="width: 360px;">
                        <span class="search-bar-icon">🔍</span>
                        <input id="patientDirectorySearchInput" type="text" placeholder="Search by Name, MRN (P-XXXXX), Phone..." onkeyup="filterPatientsDirectory()">
                    </div>
                    <button class="btn-primary" onclick="openNewPatientModal()">
                        <span>➕ Register Patient</span>
                    </button>
                </div>
            </div>

            <div class="glass-panel">
                <div class="panel-header">
                    <div class="panel-title">
                        <span>Registered Patient Profiles</span>
                        <span id="patientDirectoryCountBadge" class="appt-time-badge">0 Active</span>
                    </div>
                    <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.3rem 0.6rem;" onclick="loadPatientsDirectory()">
                        🔄 Refresh List
                    </button>
                </div>

                <div class="custom-table-container">
                    <table class="med-table">
                        <thead>
                            <tr>
                                <th>MRN</th>
                                <th>Patient Name</th>
                                <th>Date of Birth / Age</th>
                                <th>Contact Phone</th>
                                <th>Insurance Carrier</th>
                                <th>Policy #</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="patientsDirectoryTbody">
                            <tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading patient directory...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

        </div>


        <!-- ==================================================================== -->
        <!-- VIEW 4: AI VOICE AGENT CALL CONSOLE                                  -->
        <!-- ==================================================================== -->
        <div id="viewVoiceAgentConsole" class="portal-view">
            
            <div class="doctor-selector-bar">
                <div>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 0.5rem;">
                        <span>🎙️ Aura Virtual Voice Receptionist</span>
                        <span class="badge-confirmed" style="font-size: 0.72rem;">TRILINGUAL (EN, HI, PA)</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">
                        Full-duplex real-time voice pipeline: Azure Speech STT &rarr; GPT-4o Intent & Tools &rarr; Azure Speech TTS
                    </div>
                </div>

                <div style="display: flex; align-items: center; gap: 0.8rem;">
                    <a href="/api/telephony/web-caller" target="_blank" class="btn-secondary" style="text-decoration: none;">
                        <span>🚀 Open Standalone Calling Studio</span>
                    </a>
                </div>
            </div>

            <div class="voice-console-grid">
                
                <!-- Left Column: Audio Controls & Device Status -->
                <div class="glass-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span>🎧 Phone Audio Console</span>
                        </div>
                    </div>

                    <div class="form-group" style="margin-bottom: 0.85rem;">
                        <label>Incoming Caller ID (ANI Auto-Lookup):</label>
                        <select id="voiceConsoleCallerIdSelect" class="form-control" style="font-size: 0.82rem;">
                            <option value="+91-98765-43210">Aarav Sharma (+91-98765-43210) — Has Upcoming Appt</option>
                            <option value="+91-98123-45678">Priya Patel (+91-98123-45678) — Returning Patient</option>
                            <option value="+91-99887-76655">Vikram Malhotra (+91-99887-76655) — Returning Patient</option>
                            <option value="">Unknown / Anonymous Caller (Default Greeting)</option>
                        </select>
                    </div>

                    <div class="form-group" style="margin-bottom: 1.25rem;">
                        <label>Microphone Hardware:</label>
                        <select id="voiceConsoleMicSelect" class="form-control" style="font-size: 0.82rem;">
                            <option>Default System Microphone</option>
                        </select>
                    </div>

                    <div id="voiceCallStatusBadge" style="background: var(--bg-card-subtle); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 0.85rem; text-align: center; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem; font-weight: 600;">
                        Ready to connect. Click "Start Voice Call" to begin speaking with Aura.
                    </div>

                    <!-- Live Audio Waveform Canvas -->
                    <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 0.75rem; margin-bottom: 1.25rem; text-align: center;">
                        <canvas id="voiceWaveformCanvas" width="320" height="60" style="width: 100%; height: 60px;"></canvas>
                        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.3rem;">Real-time audio frequency monitor</div>
                    </div>

                    <button id="btnStartVoiceCall" class="btn-primary" style="width: 100%; justify-content: center; padding: 0.85rem; font-size: 0.95rem; margin-bottom: 0.75rem;" onclick="startConsoleVoiceCall()">
                        <span>🎙️ Start Voice Call (Instant)</span>
                    </button>
                    <button id="btnEndVoiceCall" class="btn-danger" style="width: 100%; justify-content: center; padding: 0.85rem; font-size: 0.95rem; display: none;" onclick="endConsoleVoiceCall()">
                        <span>🔴 End Voice Call</span>
                    </button>

                    <div style="margin-top: 1.5rem;">
                        <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.6rem;">
                            Quick Spoken Prompts to Try:
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                            <button class="btn-secondary" style="font-size: 0.78rem; text-align: left; justify-content: flex-start;" onclick="simulateSpokenPrompt('What are Dr. Ananya Rao\'s open slots for cardiology tomorrow?')">
                                💬 "What are Dr. Ananya Rao's open slots for cardiology tomorrow?"
                            </button>
                            <button class="btn-secondary" style="font-size: 0.78rem; text-align: left; justify-content: flex-start;" onclick="simulateSpokenPrompt('I have knee joint pain and need an appointment with Dr. Vikram Sen.')">
                                💬 "I have knee pain, need Dr. Vikram Sen."
                            </button>
                            <button class="btn-secondary" style="font-size: 0.78rem; text-align: left; justify-content: flex-start;" onclick="simulateSpokenPrompt('Book an appointment with Dr. Rajesh Iyer tomorrow at 10:00 AM for Aarav Sharma.')">
                                💬 "Book Dr. Rajesh tomorrow at 10:00 AM for Aarav Sharma."
                            </button>
                            <button class="btn-secondary" style="font-size: 0.78rem; text-align: left; justify-content: flex-start;" onclick="simulateSpokenPrompt('नमस्ते, क्या मुझे कल डॉक्टर सुनीता कपूर के लिए अपॉइंटमेंट मिल सकता है?')">
                                💬 "बातचीत हिंदी में करें (Speak in Hindi)"
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Right Column: Live Conversation Stream -->
                <div class="glass-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span>💬 Live Agentic Conversation Stream</span>
                        </div>
                        <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.3rem 0.6rem;" onclick="clearVoiceTranscript()">
                            🧹 Clear Log
                        </button>
                    </div>

                    <div id="voiceTranscriptFeed" class="transcript-feed">
                        <div style="color: var(--text-muted); font-style: italic; text-align: center; margin-top: 5rem;">
                            Conversation turns and tool execution badges will appear here live as you speak...
                        </div>
                    </div>
                </div>

            </div>

        </div>

    </main>


    <!-- ==================================================================== -->
    <!-- MODAL 1: PATIENT MEDICAL CHART & LONGITUDINAL SOAP NOTES             -->
    <!-- ==================================================================== -->
    <div id="modalPatientChart" class="modal-overlay">
        <div class="modal-card">
            <div class="modal-header">
                <div style="font-size: 1.15rem; font-weight: 700; color: var(--text-main);">
                    📂 Longitudinal Patient Medical Record
                </div>
                <button class="close-btn" onclick="closePatientChart()">&times;</button>
            </div>
            <div class="modal-body" id="patientChartModalBody">
                <div style="text-align: center; padding: 2rem; color: var(--text-muted);">Fetching longitudinal medical records...</div>
            </div>
        </div>
    </div>


    <!-- ==================================================================== -->
    <!-- MODAL 2: DIRECT APPOINTMENT BOOKING                                  -->
    <!-- ==================================================================== -->
    <div id="modalDirectBooking" class="modal-overlay">
        <div class="modal-card" style="max-width: 540px;">
            <div class="modal-header">
                <div style="font-size: 1.15rem; font-weight: 700; color: var(--text-main);">
                    📅 Book Clinic Appointment
                </div>
                <button class="close-btn" onclick="closeDirectBookingModal()">&times;</button>
            </div>
            <div class="modal-body">
                <form id="directBookingForm" onsubmit="submitDirectBooking(event)">
                    <div class="form-group" style="margin-bottom: 1rem;">
                        <label>Patient *</label>
                        <select id="directBookPatientSelect" class="form-control" required>
                            <!-- Populated dynamically -->
                        </select>
                    </div>

                    <div class="form-group" style="margin-bottom: 1rem;">
                        <label>Attending Clinician *</label>
                        <select id="directBookDoctorSelect" class="form-control" required>
                            <!-- Populated dynamically -->
                        </select>
                    </div>

                    <div class="form-grid" style="margin-bottom: 1rem;">
                        <div class="form-group">
                            <label>Appointment Date (YYYY-MM-DD) *</label>
                            <input id="directBookDate" type="date" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label>Appointment Time *</label>
                            <select id="directBookTime" class="form-control" required>
                                <option value="09:00 AM">09:00 AM</option>
                                <option value="10:00 AM">10:00 AM</option>
                                <option value="11:30 AM">11:30 AM</option>
                                <option value="02:00 PM">02:00 PM</option>
                                <option value="03:30 PM">03:30 PM</option>
                                <option value="04:30 PM">04:30 PM</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-group" style="margin-bottom: 1.5rem;">
                        <label>Reason for Consultation</label>
                        <input id="directBookReason" type="text" class="form-control" placeholder="e.g. Hypertension review, Routine checkup, Skin rash">
                    </div>

                    <div style="display: flex; justify-content: flex-end; gap: 0.8rem;">
                        <button type="button" class="btn-secondary" onclick="closeDirectBookingModal()">Cancel</button>
                        <button type="submit" class="btn-primary">Confirm Booking & Reserve Slot</button>
                    </div>
                </form>
            </div>
        </div>
    </div>


    <!-- ==================================================================== -->
    <!-- MODAL 3: ONBOARD NEW PATIENT                                         -->
    <!-- ==================================================================== -->
    <div id="modalNewPatient" class="modal-overlay">
        <div class="modal-card">
            <div class="modal-header">
                <div style="font-size: 1.15rem; font-weight: 700; color: var(--text-main);">
                    ➕ Onboard New Clinic Patient
                </div>
                <button class="close-btn" onclick="closeNewPatientModal()">&times;</button>
            </div>
            <div class="modal-body">
                <form id="newPatientForm" onsubmit="submitNewPatient(event)">
                    <div class="form-grid" style="margin-bottom: 1rem;">
                        <div class="form-group">
                            <label>Legal First Name *</label>
                            <input id="newPatFirstName" type="text" class="form-control" required placeholder="e.g. Rohan">
                        </div>
                        <div class="form-group">
                            <label>Legal Last Name *</label>
                            <input id="newPatLastName" type="text" class="form-control" required placeholder="e.g. Verma">
                        </div>
                    </div>

                    <div class="form-grid" style="margin-bottom: 1rem;">
                        <div class="form-group">
                            <label>Date of Birth (YYYY-MM-DD) *</label>
                            <input id="newPatDOB" type="text" class="form-control" required placeholder="1990-05-18">
                        </div>
                        <div class="form-group">
                            <label>Phone Number *</label>
                            <input id="newPatPhone" type="text" class="form-control" required placeholder="+91-98765-11223">
                        </div>
                    </div>

                    <div class="form-grid" style="margin-bottom: 1.5rem;">
                        <div class="form-group">
                            <label>Insurance Carrier</label>
                            <input id="newPatInsurance" type="text" class="form-control" placeholder="e.g. Star Health, HDFC ERGO">
                        </div>
                        <div class="form-group">
                            <label>Policy Number</label>
                            <input id="newPatPolicy" type="text" class="form-control" placeholder="e.g. POL-9921">
                        </div>
                    </div>

                    <div style="display: flex; justify-content: flex-end; gap: 0.8rem;">
                        <button type="button" class="btn-secondary" onclick="closeNewPatientModal()">Cancel</button>
                        <button type="submit" class="btn-primary">Register Patient & Assign MRN</button>
                    </div>
                </form>
            </div>
        </div>
    </div>


    <!-- ==================================================================== -->
    <!-- MODAL 4: ONBOARD NEW DOCTOR                                          -->
    <!-- ==================================================================== -->
    <div id="modalAddDoctor" class="modal-overlay">
        <div class="modal-card">
            <div class="modal-header">
                <div style="font-size: 1.15rem; font-weight: 700; color: var(--text-main);">
                    👨‍⚕️ Onboard New Clinician to Roster
                </div>
                <button class="close-btn" onclick="closeAddDoctorModal()">&times;</button>
            </div>
            <div class="modal-body">
                <form id="addDoctorForm" onsubmit="submitNewDoctor(event)">
                    <div class="form-grid" style="margin-bottom: 1rem;">
                        <div class="form-group">
                            <label>Doctor Full Name *</label>
                            <input id="newDocName" type="text" class="form-control" required placeholder="e.g. Dr. Kavita Reddy">
                        </div>
                        <div class="form-group">
                            <label>Clinical Specialty *</label>
                            <input id="newDocSpecialty" type="text" class="form-control" required placeholder="e.g. Neurology, ENT, Oncology">
                        </div>
                    </div>

                    <div class="form-grid" style="margin-bottom: 1rem;">
                        <div class="form-group">
                            <label>Qualifications *</label>
                            <input id="newDocQual" type="text" class="form-control" required placeholder="e.g. MBBS, MD, DM (Neurology)">
                        </div>
                        <div class="form-group">
                            <label>Department *</label>
                            <input id="newDocDept" type="text" class="form-control" required placeholder="e.g. Department of Neurological Sciences">
                        </div>
                    </div>

                    <div class="form-grid" style="margin-bottom: 1.5rem;">
                        <div class="form-group">
                            <label>Title / Badge</label>
                            <input id="newDocBadge" type="text" class="form-control" placeholder="e.g. Consultant Neurologist">
                        </div>
                        <div class="form-group">
                            <label>Avatar Emoji</label>
                            <input id="newDocAvatar" type="text" class="form-control" value="🧠">
                        </div>
                    </div>

                    <div style="display: flex; justify-content: flex-end; gap: 0.8rem;">
                        <button type="button" class="btn-secondary" onclick="closeAddDoctorModal()">Cancel</button>
                        <button type="submit" class="btn-primary">Add Clinician & Seed Schedules</button>
                    </div>
                </form>
            </div>
        </div>
    </div>


    <!-- ==================================================================== -->
    <!-- CLIENT JAVASCRIPT APPLICATION LOGIC                                  -->
    <!-- ==================================================================== -->
    <script>
        // ---------------------------------------------------------------------
        // Global State
        // ---------------------------------------------------------------------
        let clinicDoctors = [];
        let activeDoctor = null;
        let activeAppointments = [];
        let clinicPatients = [];
        let activeSoapNote = null;
        let isRecording = false;
        let recognition = null;
        let speechFinalTranscript = '';
        let baseTranscriptPrefix = '';

        // Voice Agent WebSocket & Audio Context
        let consoleAudioWs = null;
        let consoleAudioCtx = null;
        let consoleMicStream = null;
        let consoleProcessorNode = null;
        let consoleAnalyserNode = null;
        let isVoiceCallActive = false;

        // ---------------------------------------------------------------------
        // Theme Engine (Light Mode Primary Default + Dark Mode Option)
        // ---------------------------------------------------------------------
        function initTheme() {
            const savedTheme = localStorage.getItem('auracare_theme') || 'light';
            setTheme(savedTheme);
        }

        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('auracare_theme', theme);
            const toggleIcon = document.getElementById('themeToggleIcon');
            const toggleText = document.getElementById('themeToggleText');
            if (theme === 'dark') {
                if (toggleIcon) toggleIcon.innerText = '☀️';
                if (toggleText) toggleText.innerText = 'Light Mode';
            } else {
                if (toggleIcon) toggleIcon.innerText = '🌙';
                if (toggleText) toggleText.innerText = 'Dark Mode';
            }
        }

        function toggleTheme() {
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            setTheme(current === 'dark' ? 'light' : 'dark');
        }

        // ---------------------------------------------------------------------
        // Role & Tab Switching
        // ---------------------------------------------------------------------
        function switchPortalTab(tabName) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.portal-view').forEach(view => view.classList.remove('active-view'));

            if (tabName === 'doctor') {
                document.getElementById('tabBtnDoctor').classList.add('active');
                document.getElementById('viewDoctorPortal').classList.add('active-view');
                loadDoctorAppointments();
            } else if (tabName === 'receptionist') {
                document.getElementById('tabBtnReceptionist').classList.add('active');
                document.getElementById('viewReceptionistPortal').classList.add('active-view');
                loadReceptionistData();
            } else if (tabName === 'patients') {
                document.getElementById('tabBtnPatients').classList.add('active');
                document.getElementById('viewPatientsDirectory').classList.add('active-view');
                loadPatientsDirectory();
            } else if (tabName === 'voice') {
                document.getElementById('tabBtnVoice').classList.add('active');
                document.getElementById('viewVoiceAgentConsole').classList.add('active-view');
                populateMicrophones();
            }
        }

        // ---------------------------------------------------------------------
        // Initialization on Load
        // ---------------------------------------------------------------------
        window.addEventListener('DOMContentLoaded', async () => {
            initTheme();
            await loadClinicDoctors();
            await loadDoctorAppointments();
            await loadReceptionistData();
            await loadPatientsDirectory();
            initDirectBookingDate();
        });

        function initDirectBookingDate() {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const iso = tomorrow.toISOString().split('T')[0];
            const el = document.getElementById('directBookDate');
            if (el) el.value = iso;
        }

        // ---------------------------------------------------------------------
        // Clinicians Data & Dropdowns
        // ---------------------------------------------------------------------
        async function loadClinicDoctors() {
            try {
                const res = await fetch('/api/dashboard/doctors');
                if (res.ok) {
                    clinicDoctors = await res.json();
                } else {
                    clinicDoctors = [];
                }
            } catch (err) {
                console.warn("Failed to fetch doctors:", err);
            }

            const selector = document.getElementById('doctorSelectorDropdown');
            const bookingDocSelect = document.getElementById('directBookDoctorSelect');
            if (selector) {
                selector.innerHTML = clinicDoctors.map(d => `<option value="${d.name}">${d.name} (${d.specialty})</option>`).join('');
            }
            if (bookingDocSelect) {
                bookingDocSelect.innerHTML = clinicDoctors.map(d => `<option value="${d.name}">${d.name} - ${d.specialty}</option>`).join('');
            }

            if (clinicDoctors.length > 0) {
                activeDoctor = clinicDoctors[0];
                updateDoctorHeaderProfile(activeDoctor);
            }
        }

        function updateDoctorHeaderProfile(doc) {
            document.getElementById('docAvatar').innerText = doc.avatar || '🩺';
            document.getElementById('docDisplayName').innerText = doc.name;
            document.getElementById('docBadge').innerText = doc.badge || doc.specialty;
            document.getElementById('docDept').innerText = doc.department || 'Clinical Practice';
            document.getElementById('docQual').innerText = doc.qualification || 'MD';
        }

        function onDoctorChanged() {
            const docName = document.getElementById('doctorSelectorDropdown').value;
            const match = clinicDoctors.find(d => d.name === docName);
            if (match) {
                activeDoctor = match;
                updateDoctorHeaderProfile(activeDoctor);
                loadDoctorAppointments();
            }
        }

        // ---------------------------------------------------------------------
        // Doctor Portal: Queue & Scribe Selection
        // ---------------------------------------------------------------------
        async function loadDoctorAppointments() {
            if (!activeDoctor) return;
            const container = document.getElementById('doctorAppointmentsContainer');
            container.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 2rem;">Loading clinician queue...</div>';

            try {
                // Fetch using exact doctor route
                const res = await fetch(`/api/dashboard/doctor/${encodeURIComponent(activeDoctor.name)}/appointments`);
                if (!res.ok) throw new Error("HTTP error " + res.status);
                const appts = await res.json();
                document.getElementById('doctorApptCountBadge').innerText = `${appts.length} Patients`;

                if (!appts || appts.length === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted);">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🕒</div>
                            <div style="font-weight: 600;">No appointments for this clinician today.</div>
                            <div style="font-size: 0.8rem; margin-top: 0.4rem;">New bookings via AI Receptionist or Front Desk will appear here.</div>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = appts.map((a, idx) => `
                    <div class="appt-card ${idx === 0 ? 'active-selected' : ''}" onclick="selectPatientForScribe('${a.patient_id}', '${a.id}', '${a.appointment_date}', this)">
                        <div class="appt-card-top">
                            <span class="appt-time-badge">🕒 ${a.appointment_time}</span>
                            <span class="badge-confirmed">${a.status}</span>
                        </div>
                        <div class="patient-card-name">Patient #${a.patient_id}</div>
                        <div class="patient-card-mrn">MRN: ${a.patient_id} | Date: ${a.appointment_date}</div>
                        <div class="appt-reason-text">"${a.reason_for_visit || 'General Consultation'}"</div>
                        <div class="appt-actions-row">
                            <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.3rem 0.6rem;" onclick="event.stopPropagation(); openPatientChart('${a.patient_id}')">
                                📂 Full Chart
                            </button>
                            <button class="btn-primary" style="font-size: 0.75rem; padding: 0.3rem 0.6rem;" onclick="event.stopPropagation(); openPatientInScribe('${a.patient_id}', '${a.id}', '${a.appointment_date}')">
                                🎙️ Open in Scribe
                            </button>
                        </div>
                    </div>
                `).join('');

                // Pre-select first patient
                if (appts.length > 0) {
                    selectPatientForScribe(appts[0].patient_id, appts[0].id, appts[0].appointment_date);
                }

            } catch (err) {
                console.error("Failed to load doctor appointments:", err);
                container.innerHTML = '<div style="color: var(--rose-500); padding: 1rem; text-align: center;">Could not load appointments. Click Refresh to retry.</div>';
                document.getElementById('doctorApptCountBadge').innerText = "0 Patients";
            }
        }

        async function selectPatientForScribe(patientId, apptId, apptDate, cardEl) {
            if (cardEl) {
                document.querySelectorAll('.appt-card').forEach(c => c.classList.remove('active-selected'));
                cardEl.classList.add('active-selected');
            }

            document.getElementById('scribeTargetPatientId').innerText = patientId;
            document.getElementById('scribeTargetDate').innerText = apptDate || new Date().toISOString().split('T')[0];

            try {
                const res = await fetch(`/api/dashboard/patients/${patientId}/chart`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('scribeTargetPatientName').innerText = `${data.patient.first_name} ${data.patient.last_name}`;
                } else {
                    document.getElementById('scribeTargetPatientName').innerText = `Patient ${patientId}`;
                }
            } catch (e) {
                document.getElementById('scribeTargetPatientName').innerText = `Patient ${patientId}`;
            }
        }

        // Seamless "Open in Scribe" handler
        async function openPatientInScribe(patientId, apptId, apptDate, patientName) {
            switchPortalTab('doctor');
            if (patientName) {
                document.getElementById('scribeTargetPatientName').innerText = patientName;
            }
            document.getElementById('scribeTargetPatientId').innerText = patientId;
            document.getElementById('scribeTargetDate').innerText = apptDate || new Date().toISOString().split('T')[0];
            
            // Clear prior draft fields
            document.getElementById('soapSubjective').value = '';
            document.getElementById('soapObjective').value = '';
            document.getElementById('soapAssessment').value = '';
            document.getElementById('soapPlan').value = '';

            // Fetch patient details if needed
            if (!patientName) {
                try {
                    const res = await fetch(`/api/dashboard/patients/${patientId}/chart`);
                    if (res.ok) {
                        const data = await res.json();
                        document.getElementById('scribeTargetPatientName').innerText = `${data.patient.first_name} ${data.patient.last_name}`;
                    }
                } catch(e) {}
            }

            // Smooth scroll to Scribe Studio and pulse glow
            const studio = document.getElementById('scribeStudio');
            studio.scrollIntoView({ behavior: 'smooth', block: 'start' });
            studio.classList.remove('scribe-studio-highlight');
            void studio.offsetWidth; // Trigger reflow
            studio.classList.add('scribe-studio-highlight');
        }

        // ---------------------------------------------------------------------
        // Scribe Speech Recognition (Fixed: No Duplicate Word Insertion!)
        // ---------------------------------------------------------------------
        function toggleListening() {
            const btn = document.getElementById('btnListenAmbient');
            const timer = document.getElementById('recordingTimer');

            if (!isRecording) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    alert("Browser speech recognition is not supported in this browser. Please type or click 'Load Clinical Dialogue'.");
                    return;
                }

                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.lang = 'en-US';

                // Save existing text in textarea as base prefix
                const currentText = document.getElementById('rawTranscriptInput').value.trim();
                baseTranscriptPrefix = currentText ? currentText + ' ' : '';
                speechFinalTranscript = '';

                recognition.onresult = (event) => {
                    let interimTranscript = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        const piece = event.results[i][0].transcript;
                        if (event.results[i].isFinal) {
                            speechFinalTranscript += piece + ' ';
                        } else {
                            interimTranscript += piece;
                        }
                    }
                    // Deduplicated presentation
                    document.getElementById('rawTranscriptInput').value = 
                        baseTranscriptPrefix + speechFinalTranscript + (interimTranscript ? '(' + interimTranscript + ')' : '');
                };

                recognition.onerror = (e) => {
                    console.warn("Speech recognition error:", e);
                };

                recognition.start();
                isRecording = true;
                btn.classList.add('recording');
                btn.innerHTML = '<span>🛑 Stop Listening</span>';
                timer.style.display = 'inline';
            } else {
                if (recognition) {
                    recognition.stop();
                }
                isRecording = false;
                btn.classList.remove('recording');
                btn.innerHTML = '<span>🎙️ Start Ambient Scribe (Mic)</span>';
                timer.style.display = 'none';

                // Clean up final text
                const finalVal = baseTranscriptPrefix + speechFinalTranscript;
                document.getElementById('rawTranscriptInput').value = finalVal.trim();
            }
        }

        function loadSampleTranscript() {
            const sampleText = "Doctor: Good morning Aarav, how have you been feeling since your last visit? Patient: Good morning Doctor. I have had recurrent chest tightness and mild shortness of breath when climbing stairs. It lasts about 5 to 10 minutes and eases with rest. Doctor: Let us examine. Blood pressure is 142 over 88 mmHg. Heart rate is 78 beats per minute, regular rhythm. Chest is clear on auscultation. Electrocardiogram shows sinus rhythm with no acute ST changes. We will schedule a treadmill stress test and 2D echocardiogram, start Metoprolol 25mg daily, and review in two weeks.";
            document.getElementById('rawTranscriptInput').value = sampleText;
        }

        // ---------------------------------------------------------------------
        // GPT-4o SOAP Note Generation & Confirmation Gate
        // ---------------------------------------------------------------------
        async function generateSoapNote() {
            const transcript = document.getElementById('rawTranscriptInput').value.trim();
            if (!transcript) {
                alert("Please speak into the microphone or type clinical notes first.");
                return;
            }

            const patientId = document.getElementById('scribeTargetPatientId').innerText;
            const patientName = document.getElementById('scribeTargetPatientName').innerText;
            const btn = document.getElementById('btnGenerateSoap');
            btn.disabled = true;
            btn.innerText = "⏳ Generating SOAP Note with GPT-4o...";

            try {
                // Call generate endpoint
                const res = await fetch('/api/dashboard/scribe/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        transcript: transcript,
                        patient_id: (patientId && patientId !== 'None') ? patientId : 'P-10023',
                        patient_name: patientName,
                        doctor_name: activeDoctor ? activeDoctor.name : "Dr. Ananya Rao",
                        doctor_id: activeDoctor ? activeDoctor.id : "DOC-01",
                        encounter_date: document.getElementById('scribeTargetDate').innerText
                    })
                });

                const data = await res.json();
                const note = data.draft_note || data.soap || data.note;

                if (data.success && note) {
                    activeSoapNote = note;
                    document.getElementById('soapSubjective').value = note.subjective || '';
                    document.getElementById('soapObjective').value = note.objective || '';
                    document.getElementById('soapAssessment').value = note.assessment || '';
                    document.getElementById('soapPlan').value = note.plan || '';
                } else {
                    alert("SOAP generation failed: " + (data.error || data.message || "Failed to parse clinical transcript"));
                }
            } catch (err) {
                alert("Error calling GPT-4o Scribe API: " + err);
            } finally {
                btn.disabled = false;
                btn.innerText = "✨ Generate Structured SOAP Note (GPT-4o)";
            }
        }

        async function confirmAndSaveNote() {
            const patientId = document.getElementById('scribeTargetPatientId').innerText;
            if (patientId === 'None') {
                alert("Please select a patient from the queue first.");
                return;
            }

            const subjective = document.getElementById('soapSubjective').value.trim();
            const objective = document.getElementById('soapObjective').value.trim();
            const assessment = document.getElementById('soapAssessment').value.trim();
            const plan = document.getElementById('soapPlan').value.trim();

            if (!subjective || !assessment) {
                alert("Subjective history and Assessment fields cannot be empty.");
                return;
            }

            const noteId = activeSoapNote ? activeSoapNote.id : `NOTE-${patientId}-${Date.now().toString().slice(-4)}`;
            const btn = document.getElementById('btnConfirmNote');
            btn.disabled = true;
            btn.innerText = "⏳ Signing & Indexing to Azure Search...";

            const payload = {
                id: noteId,
                patient_id: patientId,
                patient_name: document.getElementById('scribeTargetPatientName').innerText,
                doctor_id: activeDoctor ? activeDoctor.id : "DOC-01",
                doctor_name: activeDoctor ? activeDoctor.name : "Dr. Ananya Rao",
                date: document.getElementById('scribeTargetDate').innerText,
                subjective: subjective,
                objective: objective,
                assessment: assessment,
                plan: plan,
                raw_transcript: document.getElementById('rawTranscriptInput').value,
                status: "CONFIRMED_BY_DOCTOR"
            };

            try {
                const res = await fetch('/api/dashboard/scribe/confirm', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.success) {
                    alert(`✅ Clinical SOAP Note Confirmed & Signed!\nPersisted to patient chart and indexed in Azure AI Search.`);
                    document.getElementById('rawTranscriptInput').value = '';
                    loadDoctorAppointments();
                } else {
                    alert("Failed to confirm note: " + result.message);
                }
            } catch (err) {
                alert("Error saving note: " + err);
            } finally {
                btn.disabled = false;
                btn.innerText = "💾 Sign & Save Clinical Note to EHR";
            }
        }

        // ---------------------------------------------------------------------
        // Receptionist Data & Appointments Table
        // ---------------------------------------------------------------------
        async function loadReceptionistData() {
            try {
                const [statsRes, apptsRes] = await Promise.all([
                    fetch('/api/dashboard/stats'),
                    fetch('/api/dashboard/appointments')
                ]);

                if (statsRes.ok) {
                    const stats = await statsRes.json();
                    document.getElementById('statTotalAppointments').innerText = 
                        (stats.total_appointments !== undefined) ? stats.total_appointments : (stats.confirmed_appointments || 0);
                    document.getElementById('statRegisteredPatients').innerText = 
                        (stats.registered_patients !== undefined) ? stats.registered_patients : (stats.total_patients || 0);
                    document.getElementById('statActiveDoctors').innerText = 
                        stats.doctors_count || clinicDoctors.length || 5;
                }

                if (apptsRes.ok) {
                    activeAppointments = await apptsRes.json();
                    renderAppointmentsTable(activeAppointments);
                }

                loadClinicianSchedules();
                loadNotificationTickets();
            } catch (e) {
                console.error("Error loading receptionist data:", e);
            }
        }

        function renderAppointmentsTable(appts) {
            document.getElementById('receptionistApptBadge').innerText = `${appts.length} Total`;
            const tbody = document.getElementById('masterAppointmentsTbody');
            if (!appts || appts.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">No appointments booked in clinic.</td></tr>';
                return;
            }

            tbody.innerHTML = appts.map(a => `
                <tr>
                    <td style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--teal-500);">${a.id}</td>
                    <td style="font-weight: 600; color: var(--text-main);">Patient #${a.patient_id}</td>
                    <td style="font-family: 'JetBrains Mono', monospace; color: var(--text-muted);">${a.patient_id}</td>
                    <td>${a.doctor_name}</td>
                    <td>${a.appointment_date} <span style="color: var(--teal-600); font-family: 'JetBrains Mono', monospace; font-weight: 600;">${a.appointment_time}</span></td>
                    <td>${a.reason_for_visit || 'General Consultation'}</td>
                    <td>
                        <span class="${a.status === 'CONFIRMED' ? 'badge-confirmed' : 'badge-cancelled'}">${a.status}</span>
                    </td>
                    <td>
                        <div style="display: flex; gap: 0.4rem;">
                            <button class="btn-secondary" style="font-size: 0.74rem; padding: 0.25rem 0.5rem;" onclick="openPatientChart('${a.patient_id}')">
                                📂 Chart
                            </button>
                            <button class="btn-primary" style="font-size: 0.74rem; padding: 0.25rem 0.5rem;" onclick="openPatientInScribe('${a.patient_id}', '${a.id}', '${a.appointment_date}')">
                                🎙️ Scribe
                            </button>
                            ${a.status === 'CONFIRMED' ? `
                                <button class="btn-danger" onclick="cancelAppointment('${a.patient_id}', '${a.id}')">
                                    Cancel
                                </button>
                            ` : `
                                <button class="btn-secondary" style="font-size: 0.74rem; padding: 0.25rem 0.5rem;" onclick="prefillRebooking('${a.patient_id}', '${a.doctor_name}')">
                                    📅 Re-Book
                                </button>
                            `}
                        </div>
                    </td>
                </tr>
            `).join('');
        }

        function filterAppointmentsTable() {
            const query = document.getElementById('searchAppointmentInput').value.toLowerCase();
            const filtered = activeAppointments.filter(a => 
                a.patient_id.toLowerCase().includes(query) ||
                a.doctor_name.toLowerCase().includes(query) ||
                (a.id && a.id.toLowerCase().includes(query)) ||
                (a.reason_for_visit && a.reason_for_visit.toLowerCase().includes(query))
            );
            renderAppointmentsTable(filtered);
        }

        async function cancelAppointment(patientId, apptId) {
            if (!confirm(`Cancel appointment ${apptId}?`)) return;
            try {
                const res = await fetch(`/api/dashboard/appointments/${apptId}/cancel?patient_id=${patientId}`, { method: 'POST' });
                const data = await res.json();
                alert(data.message || "Appointment cancelled.");
                loadReceptionistData();
                loadDoctorAppointments();
            } catch (e) {
                alert("Cancellation failed: " + e);
            }
        }

        async function loadClinicianSchedules() {
            const grid = document.getElementById('clinicianSchedulesGrid');
            try {
                const res = await fetch('/api/dashboard/schedules');
                if (!res.ok) return;
                const schedules = await res.json();
                if (!schedules || schedules.length === 0) {
                    grid.innerHTML = '<div style="color: var(--text-muted);">No schedules active.</div>';
                    return;
                }

                const grouped = {};
                schedules.forEach(s => {
                    if (!grouped[s.doctor_name]) grouped[s.doctor_name] = [];
                    grouped[s.doctor_name].push(s);
                });

                grid.innerHTML = Object.keys(grouped).map(docName => {
                    const list = grouped[docName];
                    return `
                        <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1.1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                            <div style="font-weight: 700; color: var(--text-main); margin-bottom: 0.2rem; font-size: 1rem;">${docName}</div>
                            <div style="font-size: 0.78rem; color: var(--teal-600); font-weight: 600; margin-bottom: 0.8rem;">${list[0]?.specialty || 'Specialist'}</div>
                            ${list.slice(0, 2).map(s => {
                                const openSlots = s.slots.filter(sl => !sl.is_booked);
                                return `
                                    <div style="margin-bottom: 0.6rem;">
                                        <div style="font-size: 0.75rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; margin-bottom: 0.3rem;">📅 ${s.date} (${openSlots.length} open)</div>
                                        <div style="display: flex; flex-wrap: wrap; gap: 0.35rem;">
                                            ${openSlots.map(sl => `
                                                <span style="font-size: 0.72rem; background: var(--teal-50); border: 1px solid rgba(13, 148, 136, 0.3); color: var(--teal-600); padding: 0.15rem 0.45rem; border-radius: 5px; font-family: 'JetBrains Mono', monospace; font-weight: 600;">
                                                    ${sl.slot_time}
                                                </span>
                                            `).join('')}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    `;
                }).join('');
            } catch (err) {
                console.warn("Error loading clinician schedules:", err);
            }
        }

        async function loadNotificationTickets() {
            const tbody = document.getElementById('notificationTicketsTbody');
            if (!tbody) return;
            try {
                const res = await fetch('/api/dashboard/notifications');
                if (!res.ok) return;
                const data = await res.json();
                const list = data.notifications || [];
                const badge = document.getElementById('notificationTicketsCountBadge');
                if (badge) badge.innerText = `${list.length} Dispatched`;

                if (list.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">No appointment notification tickets dispatched yet.</td></tr>';
                    return;
                }

                tbody.innerHTML = list.map(n => `
                    <tr>
                        <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: var(--teal-600);">${n.ticket_number || n.appointment_id}</td>
                        <td style="font-weight: 600; color: var(--text-main);">${n.patient_name || '--'}</td>
                        <td style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--text-main);">${n.recipient_phone || '--'}</td>
                        <td>${n.doctor_name || '--'}</td>
                        <td>${n.appointment_date || ''} <span style="color: var(--teal-600); font-family: 'JetBrains Mono', monospace; font-weight: 600;">${n.appointment_time || ''}</span></td>
                        <td>
                            <span class="badge-confirmed" style="background:#ecfdf5;color:#059669;font-size:0.75rem;padding:2px 8px;">🟢 SMS DELIVERED</span>
                        </td>
                        <td style="font-size: 0.76rem; color: var(--text-muted); max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${n.message || ''}">
                            ${n.message || ''}
                        </td>
                        <td style="font-size: 0.75rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">
                            ${n.timestamp ? new Date(n.timestamp).toLocaleTimeString() : '--'}
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.warn("Could not load notification tickets:", err);
            }
        }

        // ---------------------------------------------------------------------
        // Patients Directory (Search, Active Status, Chart Launch)
        // ---------------------------------------------------------------------
        async function loadPatientsDirectory() {
            const tbody = document.getElementById('patientsDirectoryTbody');
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading patient directory...</td></tr>';

            try {
                const res = await fetch('/api/dashboard/patients');
                if (res.ok) {
                    clinicPatients = await res.json();
                    renderPatientsDirectory(clinicPatients);
                    updateDirectBookingPatientDropdown(clinicPatients);
                } else {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--rose-500);">Failed to load patients directory.</td></tr>';
                }
            } catch (e) {
                console.error(e);
            }
        }

        function renderPatientsDirectory(patients) {
            document.getElementById('patientDirectoryCountBadge').innerText = `${patients.length} Active`;
            const tbody = document.getElementById('patientsDirectoryTbody');
            if (!patients || patients.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">No patients found.</td></tr>';
                return;
            }

            tbody.innerHTML = patients.map(p => `
                <tr>
                    <td style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--teal-600);">${p.id}</td>
                    <td>
                        <div style="font-weight: 700; color: var(--text-main); font-size: 0.92rem;">${p.first_name} ${p.last_name}</div>
                    </td>
                    <td>${p.date_of_birth}</td>
                    <td style="font-family: 'JetBrains Mono', monospace;">${p.phone_number || '--'}</td>
                    <td>${p.insurance_provider || 'Self-Pay'}</td>
                    <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;">${p.insurance_policy_number || 'N/A'}</td>
                    <td>
                        <span class="badge-active-patient">🟢 Active Patient</span>
                    </td>
                    <td>
                        <div style="display: flex; gap: 0.4rem;">
                            <button class="btn-secondary" style="font-size: 0.74rem; padding: 0.25rem 0.5rem;" onclick="openPatientChart('${p.id}')">
                                📂 Chart
                            </button>
                            <button class="btn-primary" style="font-size: 0.74rem; padding: 0.25rem 0.5rem;" onclick="openPatientInScribe('${p.id}', null, null, '${p.first_name} ${p.last_name}')">
                                🎙️ Scribe
                            </button>
                            <button class="btn-secondary" style="font-size: 0.74rem; padding: 0.25rem 0.5rem;" onclick="prefillBookingForPatient('${p.id}')">
                                📅 Book
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }

        function filterPatientsDirectory() {
            const q = document.getElementById('patientDirectorySearchInput').value.toLowerCase().trim();
            const filtered = clinicPatients.filter(p => 
                p.id.toLowerCase().includes(q) ||
                p.first_name.toLowerCase().includes(q) ||
                p.last_name.toLowerCase().includes(q) ||
                (p.phone_number && p.phone_number.includes(q)) ||
                (p.insurance_provider && p.insurance_provider.toLowerCase().includes(q))
            );
            renderPatientsDirectory(filtered);
        }

        function updateDirectBookingPatientDropdown(patients) {
            const sel = document.getElementById('directBookPatientSelect');
            if (!sel) return;
            sel.innerHTML = patients.map(p => `
                <option value="${p.id}">${p.first_name} ${p.last_name} (${p.id}) - DOB: ${p.date_of_birth}</option>
            `).join('');
        }

        // ---------------------------------------------------------------------
        // Longitudinal Patient Chart Modal
        // ---------------------------------------------------------------------
        async function openPatientChart(patientId) {
            if (!patientId || patientId === 'None') return;
            const modal = document.getElementById('modalPatientChart');
            const body = document.getElementById('patientChartModalBody');
            modal.style.display = 'flex';
            body.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Fetching longitudinal medical records...</div>';

            try {
                const res = await fetch(`/api/dashboard/patients/${patientId}/chart`);
                if (!res.ok) throw new Error("Patient chart lookup failed");
                const data = await res.json();
                const pat = data.patient;
                const notes = data.clinical_notes || [];

                body.innerHTML = `
                    <div style="background: var(--bg-card-subtle); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                            <div style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 700; color: var(--text-main);">
                                ${pat.first_name} ${pat.last_name}
                            </div>
                            <span class="appt-time-badge">${pat.id}</span>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.6rem; font-size: 0.84rem;">
                            <div><span style="color: var(--text-muted);">Date of Birth:</span> <b>${pat.date_of_birth}</b></div>
                            <div><span style="color: var(--text-muted);">Contact Phone:</span> <b>${pat.phone_number || '--'}</b></div>
                            <div><span style="color: var(--text-muted);">Insurance:</span> <b>${pat.insurance_provider || 'Self-Pay'}</b></div>
                            <div><span style="color: var(--text-muted);">Policy Number:</span> <b>${pat.insurance_policy_number || 'N/A'}</b></div>
                            <div style="grid-column: span 2;"><span style="color: var(--text-muted);">Emergency Contact:</span> <b>${pat.emergency_contact || 'None Listed'}</b></div>
                        </div>
                    </div>

                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.8rem;">
                        Longitudinal Clinical SOAP Notes (${notes.length})
                    </div>

                    ${notes.length === 0 ? `
                        <div style="text-align: center; padding: 2rem; color: var(--text-muted);">No prior clinical notes on file for this patient.</div>
                    ` : notes.map(n => `
                        <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 10px; padding: 1rem; margin-bottom: 0.8rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <div style="font-weight: 700; color: var(--teal-600); font-size: 0.9rem;">👨‍⚕️ ${n.doctor_name}</div>
                                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--text-muted);">${n.date}</div>
                            </div>
                            <div style="font-size: 0.82rem; line-height: 1.5; color: var(--text-main);">
                                <div style="margin-bottom: 0.3rem;"><b>S:</b> ${n.subjective}</div>
                                <div style="margin-bottom: 0.3rem;"><b>O:</b> ${n.objective}</div>
                                <div style="margin-bottom: 0.3rem;"><b>A:</b> ${n.assessment}</div>
                                <div><b>P:</b> ${n.plan}</div>
                            </div>
                        </div>
                    `).join('')}
                `;

            } catch (err) {
                body.innerHTML = `<div style="color: var(--rose-500); padding: 1rem;">Failed to load patient chart: ${err}</div>`;
            }
        }

        function closePatientChart() {
            document.getElementById('modalPatientChart').style.display = 'none';
        }

        // ---------------------------------------------------------------------
        // Direct Booking Modal
        // ---------------------------------------------------------------------
        function openDirectBookingModal() {
            document.getElementById('modalDirectBooking').style.display = 'flex';
        }
        function closeDirectBookingModal() {
            document.getElementById('modalDirectBooking').style.display = 'none';
        }

        function prefillBookingForPatient(patientId) {
            openDirectBookingModal();
            const sel = document.getElementById('directBookPatientSelect');
            if (sel) sel.value = patientId;
        }

        function prefillRebooking(patientId, doctorName) {
            openDirectBookingModal();
            const patSel = document.getElementById('directBookPatientSelect');
            const docSel = document.getElementById('directBookDoctorSelect');
            if (patSel) patSel.value = patientId;
            if (docSel) docSel.value = doctorName;
        }

        async function submitDirectBooking(e) {
            e.preventDefault();
            const payload = {
                patient_id: document.getElementById('directBookPatientSelect').value,
                doctor_name: document.getElementById('directBookDoctorSelect').value,
                appointment_date: document.getElementById('directBookDate').value,
                appointment_time: document.getElementById('directBookTime').value,
                reason_for_visit: document.getElementById('directBookReason').value.trim() || "General Consultation"
            };

            try {
                const res = await fetch('/api/dashboard/appointments/book', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.success) {
                    alert(`✅ Appointment Confirmed!\nTicket: ${result.appointment.id}\nClinician: ${result.appointment.doctor_name}\nDate: ${result.appointment.appointment_date} at ${result.appointment.appointment_time}`);
                    closeDirectBookingModal();
                    loadReceptionistData();
                    loadDoctorAppointments();
                } else {
                    alert("Booking failed: " + result.detail);
                }
            } catch (err) {
                alert("Error booking appointment: " + err);
            }
        }

        // ---------------------------------------------------------------------
        // Onboard New Patient Modal
        // ---------------------------------------------------------------------
        function openNewPatientModal() {
            document.getElementById('modalNewPatient').style.display = 'flex';
        }
        function closeNewPatientModal() {
            document.getElementById('modalNewPatient').style.display = 'none';
        }

        async function submitNewPatient(e) {
            e.preventDefault();
            const payload = {
                first_name: document.getElementById('newPatFirstName').value.trim(),
                last_name: document.getElementById('newPatLastName').value.trim(),
                date_of_birth: document.getElementById('newPatDOB').value.trim(),
                phone_number: document.getElementById('newPatPhone').value.trim(),
                insurance_provider: document.getElementById('newPatInsurance').value.trim() || "Self-Pay / Not Disclosed",
                insurance_policy_number: document.getElementById('newPatPolicy').value.trim() || null
            };

            try {
                const res = await fetch('/api/dashboard/patients/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.success) {
                    alert(`✅ Patient Registered!\nPermanent MRN: ${result.patient.id}\nName: ${result.patient.first_name} ${result.patient.last_name}`);
                    closeNewPatientModal();
                    document.getElementById('newPatientForm').reset();
                    loadPatientsDirectory();
                    loadReceptionistData();
                } else {
                    alert("Registration failed: " + result.message);
                }
            } catch (err) {
                alert("Error registering patient: " + err);
            }
        }

        // ---------------------------------------------------------------------
        // Onboard New Doctor Modal
        // ---------------------------------------------------------------------
        function openAddDoctorModal() {
            document.getElementById('modalAddDoctor').style.display = 'flex';
        }
        function closeAddDoctorModal() {
            document.getElementById('modalAddDoctor').style.display = 'none';
        }

        async function submitNewDoctor(e) {
            e.preventDefault();
            const payload = {
                name: document.getElementById('newDocName').value.trim(),
                specialty: document.getElementById('newDocSpecialty').value.trim(),
                qualification: document.getElementById('newDocQual').value.trim(),
                department: document.getElementById('newDocDept').value.trim(),
                badge: document.getElementById('newDocBadge').value.trim() || "Consultant Specialist",
                avatar: document.getElementById('newDocAvatar').value.trim() || "🩺"
            };

            try {
                const res = await fetch('/api/dashboard/doctors/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.success) {
                    alert(`✅ New Clinician Onboarded!\nDoctor: ${result.doctor.name}\nSpecialty: ${result.doctor.specialty}\nSchedules seeded for next 15 days.`);
                    closeAddDoctorModal();
                    document.getElementById('addDoctorForm').reset();
                    await loadClinicDoctors();
                    loadClinicianSchedules();
                } else {
                    alert("Failed to add doctor: " + result.detail);
                }
            } catch (err) {
                alert("Error onboarding doctor: " + err);
            }
        }

        // ---------------------------------------------------------------------
        // AI Voice Agent Receptionist Console (WebSocket + Web Audio)
        // ---------------------------------------------------------------------
        async function populateMicrophones() {
            try {
                const select = document.getElementById('voiceConsoleMicSelect');
                if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
                const devices = await navigator.mediaDevices.enumerateDevices();
                const audioInputs = devices.filter(d => d.kind === 'audioinput');
                if (audioInputs.length > 0) {
                    select.innerHTML = audioInputs.map((dev, idx) => 
                        `<option value="${dev.deviceId}">${dev.label || 'Microphone ' + (idx + 1)}</option>`
                    ).join('');
                }
            } catch (e) {
                console.warn("Could not list audio hardware:", e);
            }
        }

        async function startConsoleVoiceCall() {
            try {
                const statusBadge = document.getElementById('voiceCallStatusBadge');
                statusBadge.innerText = 'Connecting to Voice Receptionist pipeline...';
                document.getElementById('btnStartVoiceCall').disabled = true;

                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                try {
                    consoleAudioCtx = new AudioCtx({ sampleRate: 16000 });
                } catch(e) {
                    consoleAudioCtx = new AudioCtx();
                }
                if (consoleAudioCtx.state === 'suspended') {
                    await consoleAudioCtx.resume();
                }

                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
                });
                consoleMicStream = stream;

                const callerSelect = document.getElementById('voiceConsoleCallerIdSelect');
                const callerId = callerSelect ? callerSelect.value : '';
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const query = callerId ? `?caller_id=${encodeURIComponent(callerId)}` : '';
                const wsUrl = `${protocol}//${window.location.host}/api/telephony/ws/audio-stream${query}`;
                consoleAudioWs = new WebSocket(wsUrl);

                consoleAudioWs.onopen = () => {
                    isVoiceCallActive = true;
                    statusBadge.style.background = 'var(--emerald-50)';
                    statusBadge.style.color = 'var(--emerald-500)';
                    statusBadge.innerText = '🟢 Call Active! Speak naturally with Aura.';
                    document.getElementById('btnStartVoiceCall').style.display = 'none';
                    document.getElementById('btnEndVoiceCall').style.display = 'flex';
                    setupWaveformVisualizer(stream);
                };

                consoleAudioWs.onerror = (err) => {
                    console.error("Voice stream WS error:", err);
                    statusBadge.innerText = '⚠️ Voice stream connection error.';
                };

                consoleAudioWs.onclose = () => {
                    endConsoleVoiceCall();
                };

                consoleAudioWs.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    handleVoiceConsoleEvent(msg);
                };

                // Stream mic PCM (routed through mute gain to avoid speaker echo loopback)
                const source = consoleAudioCtx.createMediaStreamSource(stream);
                consoleProcessorNode = consoleAudioCtx.createScriptProcessor(4096, 1, 1);
                source.connect(consoleProcessorNode);
                const muteGain = consoleAudioCtx.createGain();
                muteGain.gain.value = 0;
                consoleProcessorNode.connect(muteGain);
                muteGain.connect(consoleAudioCtx.destination);

                consoleProcessorNode.onaudioprocess = (e) => {
                    if (!consoleAudioWs || consoleAudioWs.readyState !== WebSocket.OPEN) return;
                    const inputData = e.inputBuffer.getChannelData(0);

                    // Zero-Latency Client-Side RMS Barge-In VAD
                    if (currentConsoleSourceNode) {
                        let sumSq = 0;
                        for (let i = 0; i < inputData.length; i++) {
                            sumSq += inputData[i] * inputData[i];
                        }
                        const rms = Math.sqrt(sumSq / inputData.length);
                        if (rms > 0.035) {
                            stopConsoleAiPlayback();
                            try {
                                consoleAudioWs.send(JSON.stringify({ type: "client_barge_in", event: "client_barge_in" }));
                            } catch(err) {}
                        }
                    }

                    const downsampled = downsampleTo16kHz(inputData, consoleAudioCtx.sampleRate);
                    const pcm16 = new Int16Array(downsampled.length);
                    for (let i = 0; i < downsampled.length; i++) {
                        const s = Math.max(-1, Math.min(1, downsampled[i]));
                        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                    }
                    consoleAudioWs.send(pcm16.buffer);
                };

            } catch (err) {
                console.error("Call error:", err);
                document.getElementById('voiceCallStatusBadge').innerText = 'Call Error: ' + err.message;
                document.getElementById('btnStartVoiceCall').disabled = false;
            }
        }

        function endConsoleVoiceCall() {
            isVoiceCallActive = false;
            stopConsoleAiPlayback();
            if (consoleAudioWs) {
                try { consoleAudioWs.close(); } catch(e) {}
                consoleAudioWs = null;
            }
            if (consoleMicStream) {
                consoleMicStream.getTracks().forEach(t => t.stop());
                consoleMicStream = null;
            }
            if (consoleProcessorNode) {
                try { consoleProcessorNode.disconnect(); } catch(e) {}
                consoleProcessorNode = null;
            }

            const statusBadge = document.getElementById('voiceCallStatusBadge');
            statusBadge.style.background = 'var(--bg-card-subtle)';
            statusBadge.style.color = 'var(--text-muted)';
            statusBadge.innerText = 'Call ended. Click "Start Voice Call" to speak again.';
            document.getElementById('btnStartVoiceCall').disabled = false;
            document.getElementById('btnStartVoiceCall').style.display = 'flex';
            document.getElementById('btnEndVoiceCall').style.display = 'none';

            // Refresh dashboard data as appointments may have been booked
            loadReceptionistData();
            loadDoctorAppointments();
        }

        function downsampleTo16kHz(buffer, inputSampleRate) {
            if (inputSampleRate === 16000) return buffer;
            const ratio = inputSampleRate / 16000;
            const newLength = Math.round(buffer.length / ratio);
            const result = new Float32Array(newLength);
            let offsetResult = 0;
            let offsetBuffer = 0;
            while (offsetResult < result.length) {
                const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
                let accum = 0, count = 0;
                for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
                    accum += buffer[i];
                    count++;
                }
                result[offsetResult] = count > 0 ? accum / count : buffer[offsetBuffer];
                offsetResult++;
                offsetBuffer = nextOffsetBuffer;
            }
            return result;
        }

        function setupWaveformVisualizer(stream) {
            try {
                if (!consoleAudioCtx) return;
                consoleAnalyserNode = consoleAudioCtx.createAnalyser();
                consoleAnalyserNode.fftSize = 64;
                const source = consoleAudioCtx.createMediaStreamSource(stream);
                source.connect(consoleAnalyserNode);

                const canvas = document.getElementById('voiceWaveformCanvas');
                const ctx = canvas.getContext('2d');
                const dataArray = new Uint8Array(consoleAnalyserNode.frequencyBinCount);

                function drawWave() {
                    if (!isVoiceCallActive) {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        return;
                    }
                    requestAnimationFrame(drawWave);
                    consoleAnalyserNode.getByteFrequencyData(dataArray);
                    ctx.clearRect(0, 0, canvas.width, canvas.height);

                    const barWidth = (canvas.width / dataArray.length) * 2;
                    let x = 0;
                    for (let i = 0; i < dataArray.length; i++) {
                        const barHeight = (dataArray[i] / 255) * canvas.height;
                        ctx.fillStyle = '#0d9488';
                        ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
                        x += barWidth;
                    }
                }
                drawWave();
            } catch(e) {}
        }

        let currentConsoleSourceNode = null;

        function stopConsoleAiPlayback() {
            if (currentConsoleSourceNode) {
                try {
                    currentConsoleSourceNode.stop();
                    currentConsoleSourceNode.disconnect();
                } catch(e) {}
                currentConsoleSourceNode = null;
            }
        }

        function handleVoiceConsoleEvent(msg) {
            const feed = document.getElementById('voiceTranscriptFeed');
            const msgType = msg.type || msg.event;

            // 1. Instant Barge-In / Interrupt from server
            if (msgType === 'interrupt') {
                stopConsoleAiPlayback();
                return;
            }

            // 2. Real-time User Interim Speech (Client-side immediate cutoff of AI playback)
            if (msgType === 'interim') {
                stopConsoleAiPlayback();
                let interim = document.getElementById('consoleInterimDraft');
                if (!interim) {
                    interim = document.createElement('div');
                    interim.id = 'consoleInterimDraft';
                    interim.className = 'bubble-msg bubble-user';
                    interim.style.opacity = '0.75';
                    interim.style.fontStyle = 'italic';
                    interim.style.borderLeft = '3px solid var(--accent-primary)';
                    feed.appendChild(interim);
                }
                interim.innerText = `🗣️ ${msg.text}...`;
                feed.scrollTop = feed.scrollHeight;
                return;
            }

            // 3. Finalized User Speech Turn
            if (msgType === 'user' || msgType === 'speech_recognized' || msgType === 'final') {
                stopConsoleAiPlayback();
                const interim = document.getElementById('consoleInterimDraft');
                if (interim) interim.remove();
                if (!msg.text || !msg.text.trim()) return;
                const el = document.createElement('div');
                el.className = 'bubble-msg bubble-user';
                el.innerText = msg.text;
                feed.appendChild(el);
                feed.scrollTop = feed.scrollHeight;
            } else if (msgType === 'assistant' || msgType === 'agent_response') {
                const interim = document.getElementById('consoleInterimDraft');
                if (interim) interim.remove();

                if (msg.recognized_patient) {
                    const rp = msg.recognized_patient;
                    const rEl = document.createElement('div');
                    rEl.style.background = '#f0fdf4';
                    rEl.style.border = '1px solid #bbf7d0';
                    rEl.style.borderRadius = '8px';
                    rEl.style.padding = '0.65rem 0.85rem';
                    rEl.style.marginBottom = '0.75rem';
                    rEl.style.fontSize = '0.8rem';
                    rEl.style.color = '#166534';
                    let apptInfo = '';
                    if (rp.upcoming_doctor) {
                        apptInfo = `<br><span style="color:#15803d; font-size:0.75rem;">📅 Upcoming Appt: <b>${rp.upcoming_doctor}</b> (${rp.appointment_date} at ${rp.appointment_time})</span>`;
                    }
                    rEl.innerHTML = `<b>👤 Verified Caller (200ms Handshake):</b> ${rp.name} (MRN: ${rp.patient_id})${apptInfo}`;
                    feed.appendChild(rEl);
                }

                const el = document.createElement('div');
                el.className = 'bubble-msg bubble-agent';
                let extra = '';
                if (msg.tool_used) {
                    extra += `<br><span class="tool-badge-pill">⚙️ Tool: ${msg.tool_used}</span>`;
                }
                if (msg.intent) {
                    extra += ` <span class="tool-badge-pill" style="background:#e0f2fe;color:#0284c7;">🎯 Intent: ${msg.intent}</span>`;
                }
                el.innerHTML = `<b>Aura:</b> ${msg.text}${extra}`;
                feed.appendChild(el);
                feed.scrollTop = feed.scrollHeight;

                const audioData = msg.audio_base64 || msg.audio || msg.data;
                if (audioData && consoleAudioCtx) {
                    playPcmAudioBase64(audioData);
                }

                if (msg.tool_used === 'book_appointment') {
                    loadReceptionistData();
                    loadDoctorAppointments();
                    loadPatientsDirectory();
                }
            } else if (msgType === 'audio' && (msg.data || msg.audio) && consoleAudioCtx) {
                playPcmAudioBase64(msg.data || msg.audio);
            }
        }

        async function playPcmAudioBase64(b64Data) {
            try {
                // Instantly halt any previous audio source before starting new playback
                stopConsoleAiPlayback();

                if (!consoleAudioCtx) return;
                if (consoleAudioCtx.state === 'suspended') {
                    await consoleAudioCtx.resume();
                }

                if (consoleAudioWs && consoleAudioWs.readyState === WebSocket.OPEN) {
                    try { consoleAudioWs.send(JSON.stringify({ type: "playback_start" })); } catch(e) {}
                }

                const binaryStr = atob(b64Data);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {
                    bytes[i] = binaryStr.charCodeAt(i);
                }

                let audioBuffer;
                try {
                    // Azure Speech SDK default Riff16Khz16BitMonoPcm format is standard RIFF WAV
                    audioBuffer = await consoleAudioCtx.decodeAudioData(bytes.buffer.slice(0));
                } catch(decodeErr) {
                    // Resilient fallback for raw headerless PCM16
                    const int16 = new Int16Array(bytes.buffer);
                    const float32 = new Float32Array(int16.length);
                    for (let i = 0; i < int16.length; i++) {
                        float32[i] = int16[i] / 32768.0;
                    }
                    audioBuffer = consoleAudioCtx.createBuffer(1, float32.length, 16000);
                    audioBuffer.getChannelData(0).set(float32);
                }

                const source = consoleAudioCtx.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(consoleAudioCtx.destination);
                currentConsoleSourceNode = source;

                source.onended = () => {
                    if (currentConsoleSourceNode === source) {
                        currentConsoleSourceNode = null;
                        setTimeout(() => {
                            if (consoleAudioWs && consoleAudioWs.readyState === WebSocket.OPEN) {
                                try { consoleAudioWs.send(JSON.stringify({ type: "playback_end" })); } catch(e) {}
                            }
                        }, 100);
                    }
                };

                source.start(0);
            } catch(e) {
                console.warn("Audio playback error:", e);
            }
        }

        function simulateSpokenPrompt(text) {
            stopConsoleAiPlayback();
            if (!isVoiceCallActive) {
                alert("Please click 'Start Voice Call' first to establish the live voice connection with Aura.");
                return;
            }
            if (consoleAudioWs && consoleAudioWs.readyState === WebSocket.OPEN) {
                consoleAudioWs.send(JSON.stringify({ event: "simulated_speech", text: text }));
            }
        }

        function clearVoiceTranscript() {
            document.getElementById('voiceTranscriptFeed').innerHTML = `
                <div style="color: var(--text-muted); font-style: italic; text-align: center; margin-top: 5rem;">
                    Transcript cleared. Conversation turns will appear here live...
                </div>
            `;
        }
    </script>
</body>
</html>
"""
