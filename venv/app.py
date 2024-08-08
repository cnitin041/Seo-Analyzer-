from flask import Flask, request, send_file
import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, grey, green, red
from collections import Counter
import openai
import time

app = Flask(__name__)

# Set up OpenAI API key
openai.api_key = "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"

@app.route('/seo-report', methods=['POST'])
def generate_seo_report():
    # Get the URL from the request
    url = request.form['url']

    # Fetch the web page content
    try:
        response = requests.get(url)
        html_content = response.content
    except requests.exceptions.RequestException as e:
        return f"Error fetching the web page: {e}", 400

    # Parse the HTML content using BeautifulSoup
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        return f"Error parsing the HTML content: {e}", 400

    # Analyze the SEO factors
    try:
        title = soup.title.string if soup.title else ""
        meta_description = soup.find('meta', {'name': 'description'})
        if meta_description:
            meta_description = meta_description['content']
        else:
            meta_description = ""
        headings = [h.text for h in soup.find_all(['h1', 'h2', 'h3'])]
        images = [img['src'] for img in soup.find_all('img')]
        links = []
        for link in soup.find_all('a'):
            try:
                links.append(link['href'])
            except KeyError:
                continue
        word_count = len(soup.get_text().split())
        load_time = response.elapsed.total_seconds()

        # Analyze keyword usage
        text = soup.get_text().lower()
        keyword_counts = Counter(text.split())
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Analyze security
        is_https = url.startswith('https://')

        # Calculate scores based on competing websites
        competitor_urls = ["https://www.competitor1.com", "https://www.competitor2.com", "https://www.competitor3.com"]
        scores = calculate_scores(url, competitor_urls)
        title_score = scores['title_score']
        meta_description_score = scores['meta_description_score']
        headings_score = scores['headings_score']
        images_score = scores['images_score']
        links_score = scores['links_score']
        security_score = 100 if is_https else 50
        overall_score = (title_score + meta_description_score + headings_score + images_score + links_score + security_score) / 6

        # Provide suggested changes using OpenAI
        try:
            suggestions = get_suggestions(url, scores)
        except openai.error.RateLimitError as e:
            # Handle the API quota error
            print(f"Error analyzing the SEO factors: {e}")
            print("Waiting 60 seconds before retrying...")
            time.sleep(60)  # Wait for 60 seconds before retrying
            suggestions = get_suggestions(url, scores)
        except Exception as e:
            return f"Error analyzing the SEO factors: {e}", 400
    except Exception as e:
        return f"Error analyzing the SEO factors: {e}", 400

    # Generate the PDF report
    pdf_filename = 'seo_report.pdf'
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Page Title and URL
    elements.append(Paragraph('SEO Report', styles['Heading1']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f'URL: {url}', styles['BodyText']))
    elements.append(Spacer(1, 12))

    # Overall Score
    score_color = green if overall_score >= 80 else red
    elements.append(Paragraph(f'Overall Score: ', styles['Heading2']))
    elements.append(Paragraph(f"{overall_score:.0f}%", ParagraphStyle(name='ScoreText', fontSize=36, textColor=score_color)))
    elements.append(Spacer(1, 24))

    # Page Title and Meta Description
    elements.append(Paragraph(f'Title: {title}', styles['Heading2']))
    elements.append(Paragraph(f'Meta Description: {meta_description}', styles['BodyText']))
    elements.append(Spacer(1, 12))

    # Headings
    elements.append(Paragraph('Headings:', styles['Heading2']))
    for heading in headings:
        elements.append(Paragraph(heading, styles['BodyText']))
    elements.append(Spacer(1, 12))

    # Images
    elements.append(Paragraph('Images:', styles['Heading2']))
    for image in images:
        elements.append(Paragraph(image, styles['BodyText']))
    elements.append(Spacer(1, 12))

    # Links
    elements.append(Paragraph('Links:', styles['Heading2']))
    for link in links:
        elements.append(Paragraph(link, styles['BodyText']))
    elements.append(Spacer(1, 12))

    # Page Metrics
    data = [
        ['Word Count', word_count],
        ['Load Time', f"{load_time:.2f} seconds"],
        ['Security', 'HTTPS' if is_https else 'HTTP']
    ]
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), grey),
        ('TEXTCOLOR', (0,0), (-1,0), black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 14),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), '#F0F0F0'),
        ('GRID', (0,0), (-1,-1), 1, black),
    ]))
    elements.append(Paragraph('Page Metrics:', styles['Heading2']))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Top Keywords
    elements.append(Paragraph('Top Keywords:', styles['Heading2']))
    for keyword, count in top_keywords:
        elements.append(Paragraph(f"{keyword}: {count}", styles['BodyText']))
    elements.append(Spacer(1, 12))

    # Suggested Changes
    elements.append(Paragraph('Suggested Changes:', styles['Heading2']))
    for suggestion in suggestions:
        elements.append(Paragraph(suggestion, styles['BodyText']))
    elements.append(Spacer(1, 12))

    doc.build(elements)

    # Return the PDF file as a response
    return send_file(pdf_filename, as_attachment=True)

def calculate_scores(url, competitor_urls):
    # Use AI to analyze the URL and competitor URLs and calculate scores
    # This is a placeholder implementation, you would need to integrate an actual AI model here
    title_score = 80
    meta_description_score = 70
    headings_score = 90
    images_score = 85
    links_score = 75
    return {
        'title_score': title_score,
        'meta_description_score': meta_description_score,
        'headings_score': headings_score,
        'images_score': images_score,
        'links_score': links_score
    }

def get_suggestions(url, scores):
    # Use OpenAI to generate suggested changes based on the analysis
    prompt = f"Provide 3-5 suggestions to improve the SEO of the website at {url} based on the following scores:\n\nTitle score: {scores['title_score']}%\nMeta description score: {scores['meta_description_score']}%\nHeadings score: {scores['headings_score']}%\nImages score: {scores['images_score']}%\nLinks score: {scores['links_score']}%"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.7,
        )
        suggestions = response.choices[0].message.content.strip().split('\n')
    except openai.error.RateLimitError as e:
        # Handle the API quota error
        print(f"Error generating suggestions: {e}")
        suggestions = []
    
    return suggestions

if __name__ == '__main__':
    app.run(debug=True)