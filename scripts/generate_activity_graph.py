import json
import urllib.request
import ssl
from datetime import datetime, timedelta

def generate_activity_svg(username="ferdiansyahep", output_path="assets/github-activity.svg"):
    url = f"https://github-contributions-api.jogruber.de/v4/{username}?y=last"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching contributions: {e}")
        return

    total_contributions = data.get("total", {}).get("lastYear", 0)
    contributions = data.get("contributions", [])
    
    if not contributions:
        print("No contribution data found.")
        return

    # Parse dates and organize by week (columns) and day of week (rows: 0=Sun .. 6=Sat)
    # The grid has 53 weeks x 7 days
    weeks = []
    current_week = []
    
    # Pad first week if start date is not Sunday
    first_date_str = contributions[0]["date"]
    first_date = datetime.strptime(first_date_str, "%Y-%m-%d")
    first_weekday = (first_date.weekday() + 1) % 7  # 0=Sun, 1=Mon, ..., 6=Sat
    
    for _ in range(first_weekday):
        current_week.append(None)
        
    for item in contributions:
        current_week.append(item)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
            
    if current_week:
        while len(current_week) < 7:
            current_week.append(None)
        weeks.append(current_week)

    # Keep at most 53 weeks
    if len(weeks) > 53:
        weeks = weeks[-53:]

    # SVG layout constants
    width = 920
    height = 240
    card_rx = 10
    
    cell_size = 12.5
    cell_gap = 3.5
    cell_rx = 2.5
    
    start_x = 45
    start_y = 65
    
    # Colors for contribution levels (GitHub dark palette / emerald)
    level_colors = {
        0: ("#161b22", "#484f58"),  # (bg, text)
        1: ("#0e4429", "#7ee787"),
        2: ("#006d32", "#aff5b4"),
        3: ("#26a641", "#ffffff"),
        4: ("#39d353", "#04260f")
    }

    svg_parts = []
    svg_parts.append(f'<svg fill="none" viewBox="0 0 {width} {height}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append('<defs>')
    svg_parts.append('  <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">')
    svg_parts.append('    <stop offset="0%" stop-color="#0a0e17" />')
    svg_parts.append('    <stop offset="100%" stop-color="#0d1117" />')
    svg_parts.append('  </linearGradient>')
    svg_parts.append('</defs>')
    
    svg_parts.append('<style>')
    svg_parts.append("  .header-title { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 14px; font-weight: 600; fill: #58a6ff; }")
    svg_parts.append("  .badge-text { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 11px; font-weight: 600; fill: #39d353; }")
    svg_parts.append("  .month-label { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 10px; font-weight: 500; fill: #7d8590; text-anchor: middle; }")
    svg_parts.append("  .day-label { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 9px; font-weight: 500; fill: #7d8590; text-anchor: end; }")
    svg_parts.append("  .cell-text { font-family: 'SF Mono', Monaco, Menlo, Consolas, monospace; font-size: 7px; font-weight: 700; text-anchor: middle; dominant-baseline: central; }")
    svg_parts.append("  .legend-text { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 10px; fill: #7d8590; }")
    svg_parts.append('</style>')

    # Card background
    svg_parts.append(f'<rect width="{width}" height="{height}" rx="{card_rx}" fill="url(#bgGrad)" stroke="#21262d" stroke-width="1.2" />')

    # Top header
    svg_parts.append('<circle cx="28" cy="28" r="4" fill="#39d353" />')
    svg_parts.append('<text x="40" y="32" class="header-title">Contributions</text>')
    
    # Pill badge on top-right
    pill_text = f"{total_contributions:,} contributions"
    pill_w = 125
    svg_parts.append(f'<rect x="{width - pill_w - 25}" y="17" width="{pill_w}" height="22" rx="11" fill="#0e4429" stroke="#238636" stroke-width="1" />')
    svg_parts.append(f'<text x="{width - 25 - (pill_w / 2)}" y="32" text-anchor="middle" class="badge-text">{pill_text}</text>')

    # Month labels calculation
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month = None
    
    for w_idx, week in enumerate(weeks):
        for day in week:
            if day is not None:
                d_obj = datetime.strptime(day["date"], "%Y-%m-%d")
                if d_obj.month != last_month:
                    last_month = d_obj.month
                    # Only place label if it fits
                    mx = start_x + w_idx * (cell_size + cell_gap) + (cell_size / 2)
                    if mx < width - 40:
                        m_name = month_names[last_month - 1]
                        svg_parts.append(f'<text x="{mx}" y="{start_y - 8}" class="month-label">{m_name}</text>')
                break

    # Day labels (Mon = row 1, Wed = row 3, Fri = row 5)
    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for row_idx, label in day_labels.items():
        dy = start_y + row_idx * (cell_size + cell_gap) + (cell_size / 2) + 3
        svg_parts.append(f'<text x="{start_x - 8}" y="{dy}" class="day-label">{label}</text>')

    # Grid cells
    for w_idx, week in enumerate(weeks):
        for d_idx, item in enumerate(week):
            cx = start_x + w_idx * (cell_size + cell_gap)
            cy = start_y + d_idx * (cell_size + cell_gap)
            
            if item is None:
                continue
                
            count = item.get("count", 0)
            level = item.get("level", 0)
            
            bg_color, text_color = level_colors.get(level, level_colors[0])
            
            svg_parts.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell_size}" height="{cell_size}" rx="{cell_rx}" fill="{bg_color}" />')
            
            # Print count inside the cell
            count_str = str(count) if count < 1000 else f"{count//1000}k"
            tx = cx + cell_size / 2
            ty = cy + cell_size / 2 + 0.5
            svg_parts.append(f'<text x="{tx:.1f}" y="{ty:.1f}" fill="{text_color}" class="cell-text">{count_str}</text>')

    # Legend at bottom-left
    leg_y = start_y + 7 * (cell_size + cell_gap) + 12
    svg_parts.append(f'<text x="{start_x}" y="{leg_y + 8}" class="legend-text">Less</text>')
    
    leg_box_size = 9
    leg_gap = 3
    leg_start_x = start_x + 30
    
    for lvl in range(5):
        bg_col, _ = level_colors[lvl]
        bx = leg_start_x + lvl * (leg_box_size + leg_gap)
        svg_parts.append(f'<rect x="{bx}" y="{leg_y}" width="{leg_box_size}" height="{leg_box_size}" rx="2" fill="{bg_col}" />')
        
    svg_parts.append(f'<text x="{leg_start_x + 5 * (leg_box_size + leg_gap) + 4}" y="{leg_y + 8}" class="legend-text">More</text>')

    svg_parts.append('</svg>')

    svg_content = "\n".join(svg_parts)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    generate_activity_svg()
