"""PDF 리포트 생성 서비스"""
import io
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_dashboard_pdf(user, accounts, snapshots):
    """개인 대시보드 PDF 리포트 생성"""
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab 라이브러리가 설치되지 않았습니다. pip install reportlab을 실행하세요.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # 제목
    title = Paragraph(f"<b>크리에이터 대시보드 리포트</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))

    # 사용자 정보
    user_info = [
        ['이메일:', user.email],
        ['이름:', user.name or '-'],
        ['조직:', user.organization or '-'],
        ['생성일:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')]
    ]
    user_table = Table(user_info, colWidths=[2 * inch, 4 * inch])
    user_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 0.5 * inch))

    # 채널 요약
    summary_title = Paragraph("<b>채널 요약</b>", styles['Heading2'])
    elements.append(summary_title)
    elements.append(Spacer(1, 0.2 * inch))

    if accounts:
        # 헤더
        data = [['플랫폼', '계정명', '팔로워', '성장률', '참여율', '최근 게시일']]

        # 데이터 행
        for account in accounts:
            snapshot = snapshots.get(account.id, {})
            data.append([
                account.platform,
                account.account_name,
                str(snapshot.get('followers', 0)),
                f"{snapshot.get('growth_rate', 0)}%",
                f"{snapshot.get('engagement_rate', 0)}%",
                snapshot.get('last_post_date', '-')[:10] if snapshot.get('last_post_date') else '-'
            ])

        # 테이블 생성
        channel_table = Table(data, colWidths=[1 * inch, 1.5 * inch, 1 * inch, 1 * inch, 1 * inch, 1.2 * inch])
        channel_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(channel_table)
    else:
        no_data = Paragraph("채널이 연결되지 않았습니다.", styles['Normal'])
        elements.append(no_data)

    elements.append(PageBreak())

    # 상세 채널 정보
    for account in accounts:
        snapshot = snapshots.get(account.id, {})
        if not snapshot:
            continue

        # 채널 제목
        channel_title = Paragraph(f"<b>{account.platform} - {account.account_name}</b>", styles['Heading3'])
        elements.append(channel_title)
        elements.append(Spacer(1, 0.2 * inch))

        # 기본 지표
        metrics_data = [
            ['팔로워', str(snapshot.get('followers', 0))],
            ['성장률', f"{snapshot.get('growth_rate', 0)}%"],
            ['참여율', f"{snapshot.get('engagement_rate', 0)}%"],
            ['최근 게시일', snapshot.get('last_post_date', '-')[:10] if snapshot.get('last_post_date') else '-'],
            ['데이터 출처', snapshot.get('source', 'mock')]
        ]
        metrics_table = Table(metrics_data, colWidths=[2 * inch, 4 * inch])
        metrics_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.3 * inch))

        # 최근 게시물
        recent_posts = snapshot.get('recent_posts', [])
        if recent_posts:
            posts_title = Paragraph("<b>최근 게시물</b>", styles['Heading4'])
            elements.append(posts_title)
            elements.append(Spacer(1, 0.1 * inch))

            posts_data = [['제목', '게시일', '좋아요', '댓글', '조회수']]
            for post in recent_posts[:5]:  # 최대 5개만
                posts_data.append([
                    post.get('title', '-')[:30],
                    post.get('published_at', '-')[:10] if post.get('published_at') else '-',
                    str(post.get('likes', 0)),
                    str(post.get('comments', 0)),
                    str(post.get('impressions', 0))
                ])

            posts_table = Table(posts_data, colWidths=[2.5 * inch, 1.2 * inch, 0.8 * inch, 0.8 * inch, 1 * inch])
            posts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(posts_table)

        elements.append(Spacer(1, 0.5 * inch))

    # PDF 생성
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_manager_pdf(manager, creators, creator_channels, creator_snapshots):
    """기업 관리자용 통합 PDF 리포트 생성"""
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab 라이브러리가 설치되지 않았습니다. pip install reportlab을 실행하세요.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # 제목
    title = Paragraph(f"<b>기업 관리자 통합 리포트</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))

    # 관리자 정보
    manager_info = [
        ['관리자 이메일:', manager.email],
        ['이름:', manager.name or '-'],
        ['조직:', manager.organization or '-'],
        ['생성일:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')],
        ['관리 크리에이터 수:', str(len(creators))]
    ]
    manager_table = Table(manager_info, colWidths=[2.5 * inch, 4 * inch])
    manager_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(manager_table)
    elements.append(Spacer(1, 0.5 * inch))

    # 크리에이터별 리포트
    for creator in creators:
        creator_title = Paragraph(f"<b>크리에이터: {creator.name or creator.email}</b>", styles['Heading2'])
        elements.append(creator_title)
        elements.append(Spacer(1, 0.2 * inch))

        # 크리에이터 정보
        creator_info = [
            ['이메일:', creator.email],
            ['조직:', creator.organization or '-']
        ]
        creator_info_table = Table(creator_info, colWidths=[2 * inch, 4 * inch])
        creator_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ]))
        elements.append(creator_info_table)
        elements.append(Spacer(1, 0.2 * inch))

        # 채널 정보
        channels = creator_channels.get(creator.id, [])
        if channels:
            channels_data = [['플랫폼', '계정명', '팔로워', '성장률', '참여율']]
            for channel in channels:
                snapshot = creator_snapshots.get(channel.id, {})
                channels_data.append([
                    channel.platform,
                    channel.account_name,
                    str(snapshot.get('followers', 0)),
                    f"{snapshot.get('growth_rate', 0)}%",
                    f"{snapshot.get('engagement_rate', 0)}%"
                ])

            channels_table = Table(channels_data, colWidths=[1.2 * inch, 2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
            channels_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(channels_table)
        else:
            no_channels = Paragraph("채널이 연결되지 않았습니다.", styles['Normal'])
            elements.append(no_channels)

        elements.append(Spacer(1, 0.5 * inch))
        elements.append(PageBreak())

    # PDF 생성
    doc.build(elements)
    buffer.seek(0)
    return buffer
