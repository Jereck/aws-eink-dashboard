#!/usr/bin/env python3
import os
import time
from datetime import datetime, timedelta

from waveshare_epd import epd2in13_V4
import boto3
from PIL import Image, ImageDraw, ImageFont

REFRESH_INTERVAL = 3600 # seconds
AWS_REGION = "us-east-1"
FONT = ImageFont.load_default()

def get_costs():
    """Fetch AWS costs (yesterday + month-to-date)"""
    client = boto3.client("ce", region_name=AWS_REGION)

    end = datetime.utcnow.date()
    start = (end - timedelta(days=1)).strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    daily = client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end_str},
        Granularity="DAILY",
        Metrics=["UnblendedCost"]
    )
    yesterday_cost = float(
        daily["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
    )

    month_start = end.replace(day=1).strftime("%Y-%m-%d")
    monthly = client.get_cost_and_usage(
        TimePeriod={"Start": month_start, "End": end_str},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    month_cost = float(
        monthly["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
    )

    return yesterday_cost, month_cost

def get_ec2_instance_count():
    """Count running EC2 instances."""
    ec2 = boto3.client("ec2", region_name=AWS_REGION)
    reservations = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )["Reservations"]

    count = sum(len(r["Instances"]) for r in reservations)
    return count

def update_display(epd):
    """Render AWS info onto the e-ink screen."""
    # Gather data
    yesterday_cost, month_cost = get_costs()
    ec2_count = get_ec2_instance_count()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Create a blank image for drawing
    image = Image.new("1", (epd.height, epd.width), 255)  # 255 = white
    draw = ImageDraw.Draw(image)

    # Header
    draw.text((5, 0), "AWS Dashboard", font=FONT, fill=0)

    # Costs
    draw.text((5, 20), f"Yesterday: ${yesterday_cost:.2f}", font=FONT, fill=0)
    draw.text((5, 40), f"Month-to-date: ${month_cost:.2f}", font=FONT, fill=0)

    # EC2
    draw.text((5, 60), f"EC2 running: {ec2_count}", font=FONT, fill=0)

    # Footer
    draw.text((5, 100), f"Updated: {now}", font=FONT, fill=0)

    # Push to e-ink
    epd.display(epd.getbuffer(image))
    epd.sleep()

def main():
    epd = epd2in13_V4.EPD()
    epd.init(epd.FULL_UPDATE)
    epd.Clear(0xFF)

    while True:
        try:
            print("Updating AWS dashboard...")
            update_display(epd)
        except Exception as e:
            print("Error:", e)
        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()