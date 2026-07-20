"""Generate knowledge base PDF documents for the Multi-Agent AI Customer Support system."""

import os
from fpdf import FPDF

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class KBCreator(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "TechMart Support - Knowledge Base", align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def title_page(self, title, subtitle=""):
        self.add_page()
        self.ln(60)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(30, 64, 175)
        self.cell(0, 15, title, align="C")
        self.ln(18)
        if subtitle:
            self.set_font("Helvetica", "", 14)
            self.set_text_color(80, 80, 80)
            self.cell(0, 10, subtitle, align="C")
            self.ln(12)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "TechMart Customer Support", align="C")
        self.ln(6)
        self.cell(0, 8, "Version 2.0 | Updated July 2025", align="C")

    def section(self, heading, body):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 64, 175)
        self.cell(0, 10, heading)
        self.ln(8)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, body)
        self.ln(4)

    def qa(self, q, a):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, f"Q: {q}")
        self.ln(2)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 6, f"A: {a}")
        self.ln(5)

    def bullet(self, text):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(40, 40, 40)
        self.cell(8, 6, chr(8226))
        self.multi_cell(0, 6, text)
        self.ln(1)


def create_billing_faq():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("Billing FAQ", "Frequently Asked Billing Questions")

    pdf.add_page()
    pdf.qa(
        "What payment methods do you accept?",
        "We accept all major credit cards (Visa, MasterCard, American Express, Discover), "
        "PayPal, and bank transfers for annual plans. All payments are processed securely "
        "through Stripe. We also support Apple Pay and Google Pay for mobile users.",
    )
    pdf.qa(
        "When am I billed?",
        "Monthly subscribers are billed on the same date each month as their initial signup. "
        "Annual subscribers are billed once per year on the anniversary of their signup date. "
        "You will receive an email receipt for every transaction.",
    )
    pdf.qa(
        "Can I change my billing cycle?",
        "Yes. You can switch from monthly to annual billing at any time from Settings > Billing. "
        "When switching to annual, you will receive a prorated credit for the remaining days "
        "of your current monthly period. Switching from annual to monthly takes effect at "
        "the end of your current annual period.",
    )
    pdf.qa(
        "What happens if my payment fails?",
        "If a payment fails, we retry the charge automatically after 24 hours, then again after "
        "3 days and 7 days. You will receive an email notification after each failed attempt. "
        "After 3 failed attempts, your account will be downgraded to the free tier, but your "
        "data is preserved for 30 days.",
    )
    pdf.qa(
        "How do I update my credit card?",
        "Go to Settings > Billing > Payment Method. Click 'Update Card' and enter your new "
        "card details. The new card will be charged starting from your next billing cycle. "
        "Your old card will no longer be used after the update.",
    )
    pdf.qa(
        "Do you offer refunds?",
        "We offer a full refund within 7 days of any new charge if you are not satisfied. "
        "Refund requests after 7 days are evaluated on a case-by-case basis. See our "
        "Refund Policy document for complete details.",
    )
    pdf.qa(
        "Are there any hidden fees?",
        "No. The price you see on our pricing page is the price you pay. There are no setup "
        "fees, hidden charges, or overage fees. All plan features are clearly listed on the "
        "pricing page.",
    )
    pdf.qa(
        "How do I get an invoice?",
        "Invoices are automatically generated for every payment and sent to your registered "
        "email. You can also download invoices from Settings > Billing > Invoice History. "
        "Invoices include your company name and tax ID if you have added them to your profile.",
    )
    pdf.output(os.path.join(OUTPUT_DIR, "Billing_FAQ.pdf"))


def create_refund_policy():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("Refund Policy", "Complete Refund Terms and Conditions")

    pdf.add_page()
    pdf.section("1. Overview",
        "TechMart is committed to customer satisfaction. This document outlines our refund "
        "policy for all subscription plans and one-time purchases made through our platform.")
    pdf.section("2. Eligibility for Full Refund",
        "- Requests made within 7 days of the original charge\n"
        "- Account has not violated our Terms of Service\n"
        "- Refund applies to the most recent charge only\n"
        "- Annual plans: full refund within 14 days of initial purchase")
    pdf.section("3. Partial Refunds",
        "- Annual subscribers who cancel mid-term receive a prorated refund for the unused "
        "portion minus a 10% administrative fee\n"
        "- Monthly subscribers who cancel within the first 48 hours receive a full refund\n"
        "- Enterprise plans: subject to the terms of the signed contract")
    pdf.section("4. Non-Refundable Items",
        "- Add-on purchases made more than 30 days ago\n"
        "- Custom integration development fees\n"
        "- Training sessions that have already been delivered\n"
        "- Data migration services completed successfully")
    pdf.section("5. How to Request a Refund",
        "1. Log in to your TechMart account\n"
        "2. Navigate to Settings > Billing > Request Refund\n"
        "3. Select the charge you want refunded\n"
        "4. Provide a reason for the refund request\n"
        "5. Submit the request\n\n"
        "Alternatively, email support@techmart.com with your account email and the transaction ID.")
    pdf.section("6. Refund Processing Time",
        "- Credit card refunds: 5-10 business days\n"
        "- PayPal refunds: 3-5 business days\n"
        "- Bank transfers: 7-14 business days\n\n"
        "You will receive an email confirmation once the refund has been processed.")
    pdf.section("7. Disputes",
        "If you disagree with a refund decision, you may appeal by contacting our support team "
        "within 30 days. All disputes are reviewed by a senior support manager within 48 hours.")
    pdf.output(os.path.join(OUTPUT_DIR, "RefundPolicy.pdf"))


def create_subscription_plans():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("Subscription Plans", "Plan Comparison and Feature Details")

    pdf.add_page()
    pdf.section("Free Tier",
        "Price: $0/month\n"
        "- 50 AI conversations per month\n"
        "- Basic intent detection\n"
        "- Community support\n"
        "- 1 user seat\n"
        "- 100 MB storage\n"
        "- Standard response time (5-10 seconds)")
    pdf.section("Starter Plan",
        "Price: $29/month or $290/year (save 17%)\n"
        "- 500 AI conversations per month\n"
        "- All AI agents enabled (billing, technical, product, complaint, FAQ)\n"
        "- Email support with 24-hour response time\n"
        "- 5 user seats\n"
        "- 2 GB storage\n"
        "- Fast response time (2-5 seconds)\n"
        "- Basic analytics dashboard\n"
        "- 1 knowledge base with up to 50 documents")
    pdf.section("Professional Plan",
        "Price: $79/month or $790/year (save 17%)\n"
        "- Unlimited AI conversations\n"
        "- All Starter features\n"
        "- Priority support with 4-hour response time\n"
        "- 25 user seats\n"
        "- 10 GB storage\n"
        "- Priority response time (1-3 seconds)\n"
        "- Advanced analytics with custom reports\n"
        "- Unlimited knowledge base documents\n"
        "- Custom AI agent training\n"
        "- API access (1,000 calls/day)\n"
        "- Webhook integrations")
    pdf.section("Enterprise Plan",
        "Price: Custom pricing (contact sales)\n"
        "- All Professional features\n"
        "- Dedicated support with 1-hour response time\n"
        "- Unlimited user seats\n"
        "- 100 GB storage\n"
        "- Fastest response time (<1 second)\n"
        "- Custom AI model fine-tuning\n"
        "- Unlimited API access\n"
        "- SSO and SAML integration\n"
        "- SLA guarantee (99.9% uptime)\n"
        "- Dedicated account manager\n"
        "- On-premise deployment option\n"
        "- Custom integrations")
    pdf.section("Plan Upgrades",
        "You can upgrade your plan at any time from Settings > Billing. Upgrades take effect "
        "immediately, and you are charged a prorated amount for the remainder of the current "
        "billing cycle. All plan features become available within seconds of upgrade.")
    pdf.section("Plan Downgrades",
        "Downgrades take effect at the start of the next billing cycle. Your current features "
        "remain active until the end of the current period. Data exceeding the new plan limits "
        "is preserved for 30 days to allow for re-upgrade.")
    pdf.output(os.path.join(OUTPUT_DIR, "SubscriptionPlans.pdf"))


def create_payment_gateway():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("Payment Gateway Guide", "Technical Integration Documentation")

    pdf.add_page()
    pdf.section("Supported Gateways",
        "TechMart integrates with the following payment providers:\n\n"
        "- Stripe (Primary) - All card payments, Apple Pay, Google Pay\n"
        "- PayPal - Express checkout and recurring billing\n"
        "- Square - In-person payments (enterprise only)\n"
        "- Wire Transfer - Annual enterprise plans only")
    pdf.section("Stripe Integration",
        "Our primary payment processor is Stripe. All card data is tokenized and never "
        "stored on our servers. PCI DSS Level 1 compliant.\n\n"
        "API Version: 2024-12-18\n"
        "Currency: USD (primary), EUR, GBP, CAD, AUD supported\n"
        "Webhook endpoint: https://api.techmart.com/webhooks/stripe")
    pdf.section("Payment Flow",
        "1. User selects a plan from the pricing page\n"
        "2. User enters payment details on the Stripe-hosted checkout page\n"
        "3. Stripe tokenizes the card and returns a payment method ID\n"
        "4. TechMart creates a subscription via the Stripe API\n"
        "5. Confirmation email is sent to the user\n"
        "6. Account is upgraded immediately upon successful payment")
    pdf.section("Webhook Events",
        "TechMart listens for the following Stripe webhook events:\n\n"
        "- payment_intent.succeeded\n"
        "- payment_intent.payment_failed\n"
        "- customer.subscription.created\n"
        "- customer.subscription.updated\n"
        "- customer.subscription.deleted\n"
        "- invoice.paid\n"
        "- invoice.payment_failed\n\n"
        "All webhook payloads are verified using Stripe signature verification.")
    pdf.section("Error Handling",
        "Common payment errors and their resolutions:\n\n"
        "card_declined: Advise the customer to check card details or use another card.\n"
        "insufficient_funds: Customer needs to use a card with sufficient balance.\n"
        "expired_card: Customer must update their card details.\n"
        "incorrect_cvc: Customer should re-enter the CVC from the back of their card.\n"
        "processing_error: Temporary Stripe error. Retry the payment after a few minutes.\n"
        "authentication_required: Customer must complete 3D Secure authentication.")
    pdf.section("Testing",
        "Use these test card numbers in sandbox mode:\n\n"
        "Success: 4242 4242 4242 4242\n"
        "Decline: 4000 0000 0000 0002\n"
        "Requires 3DS: 4000 0025 0000 3155\n"
        "Insufficient funds: 4000 0000 0000 9995\n\n"
        "Sandbox API key: sk_test_... (available in developer settings)")
    pdf.output(os.path.join(OUTPUT_DIR, "PaymentGatewayGuide.pdf"))


def create_invoice_guide():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("Invoice Guide", "Understanding Your TechMart Invoices")

    pdf.add_page()
    pdf.section("Invoice Overview",
        "Every payment generates an invoice automatically. Invoices are sent to your registered "
        "email address and are also available for download in your account settings.")
    pdf.section("Invoice Components",
        "Each invoice contains the following information:\n\n"
        "- Invoice number (format: TM-YYYY-XXXXXX)\n"
        "- Invoice date and due date\n"
        "- Your account details (name, email, company)\n"
        "- Plan name and billing period\n"
        "- Line items with quantities and prices\n"
        "- Applicable taxes (based on your location)\n"
        "- Total amount charged\n"
        "- Payment method used\n"
        "- Transaction ID from the payment processor")
    pdf.section("Accessing Your Invoices",
        "1. Log in to your TechMart account\n"
        "2. Go to Settings > Billing > Invoice History\n"
        "3. Click the download icon next to any invoice\n"
        "4. Invoices are available as PDF files\n\n"
        "You can also set up automatic invoice forwarding to your accounting email address "
        "in Settings > Billing > Preferences.")
    pdf.section("Tax Information",
        "TechMart charges applicable sales tax or VAT based on your billing address. "
        "Tax rates are determined automatically using your location.\n\n"
        "To add your tax ID (VAT/GST number) to invoices:\n"
        "1. Go to Settings > Billing > Tax Details\n"
        "2. Enter your tax registration number\n"
        "3. Select your country and tax type\n"
        "4. Save changes\n\n"
        "Your tax ID will appear on all future invoices.")
    pdf.section("Currency and Exchange Rates",
        "Invoices are issued in USD by default. If you are paying in another currency, "
        "the exchange rate used is the rate at the time of the transaction. You can view "
        "the original charge amount and the converted amount on your invoice.")
    pdf.section("Disputing an Invoice",
        "If you believe an invoice is incorrect, contact our billing team at "
        "billing@techmart.com within 30 days of the invoice date. Include the invoice "
        "number and a description of the discrepancy. We will review and resolve the "
        "dispute within 5 business days.")
    pdf.output(os.path.join(OUTPUT_DIR, "InvoiceGuide.pdf"))


def create_billing_errors():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("Billing Errors", "Troubleshooting Payment Issues")

    pdf.add_page()
    pdf.section("Common Billing Errors",
        "This guide covers the most frequently encountered billing errors and their "
        "step-by-step resolutions.")
    pdf.section("Error: card_declined",
        "Cause: The issuing bank rejected the transaction.\n\n"
        "Resolution steps:\n"
        "1. Verify the card number, expiration date, and CVC are correct\n"
        "2. Ensure the card has sufficient funds or credit available\n"
        "3. Check if the card has international transactions enabled\n"
        "4. Contact the issuing bank to authorize the transaction\n"
        "5. Try a different payment method")
    pdf.section("Error: expired_card",
        "Cause: The card on file has expired.\n\n"
        "Resolution steps:\n"
        "1. Go to Settings > Billing > Payment Method\n"
        "2. Click 'Update Card'\n"
        "3. Enter the new card details\n"
        "4. The next billing attempt will use the updated card")
    pdf.section("Error: insufficient_funds",
        "Cause: The card does not have enough balance to cover the charge.\n\n"
        "Resolution steps:\n"
        "1. Add funds to the card or use a different card\n"
        "2. Consider downgrading to a lower plan temporarily\n"
        "3. Contact support@techmart.com if you need a payment extension")
    pdf.section("Error: subscription_unpaid",
        "Cause: The subscription invoice was not paid after multiple attempts.\n\n"
        "Resolution steps:\n"
        "1. Update your payment method immediately\n"
        "2. Go to Settings > Billing > Retry Payment\n"
        "3. If the issue persists, contact billing support\n"
        "4. Note: Your account is downgraded to free tier after 3 failed retries")
    pdf.section("Error: duplicate_charge",
        "Cause: The customer was charged twice for the same billing period.\n\n"
        "Resolution steps:\n"
        "1. Check your bank statement for the exact charge amounts and timestamps\n"
        "2. Contact support@techmart.com with both transaction IDs\n"
        "3. We will investigate and issue a refund for the duplicate charge within 48 hours\n"
        "4. You will receive email confirmation of the refund")
    pdf.section("Error: invoice_already_paid",
        "Cause: The system attempted to charge for an already-paid invoice.\n\n"
        "Resolution steps:\n"
        "1. This is usually a temporary sync issue\n"
        "2. Wait 30 minutes and check your billing history\n"
        "3. If the duplicate charge appears, contact support with the invoice number")
    pdf.section("Preventing Billing Errors",
        "- Keep your payment method information up to date\n"
        "- Ensure your card supports recurring international transactions\n"
        "- Set up payment failure notifications in Settings > Billing > Preferences\n"
        "- Add a backup payment method in case the primary fails\n"
        "- Review your billing history monthly for any discrepancies")
    pdf.output(os.path.join(OUTPUT_DIR, "BillingErrors.pdf"))


def create_company_policies():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("Company Policies", "TechMart Terms and Operational Guidelines")

    pdf.add_page()
    pdf.section("1. Privacy Policy",
        "TechMart collects and processes personal data in accordance with GDPR, CCPA, "
        "and other applicable privacy regulations. We collect only the data necessary to "
        "provide our services, including: account information (name, email), usage data "
        "(conversation logs, feature usage), and payment information (processed by Stripe, "
        "never stored on our servers). Data is encrypted at rest and in transit using "
        "AES-256 and TLS 1.3 respectively.")
    pdf.section("2. Terms of Service",
        "By using TechMart, you agree to: use the platform only for lawful purposes, "
        "not attempt to reverse-engineer or exploit the AI systems, maintain the "
        "confidentiality of your account credentials, and comply with all applicable laws. "
        "We reserve the right to suspend accounts that violate these terms. Users must be "
        "at least 18 years old or have parental consent.")
    pdf.section("3. Data Retention",
        "- Active account data: Retained while the account is active\n"
        "- Conversation logs: Retained for 90 days after last activity\n"
        "- Knowledge base documents: Retained until manually deleted\n"
        "- Payment records: Retained for 7 years (regulatory requirement)\n"
        "- Deleted account data: Permanently erased within 30 days of deletion request")
    pdf.section("4. Acceptable Use Policy",
        "Users may not: upload malicious content or malware, attempt to extract proprietary "
        "AI models or training data, use the platform for spam or phishing, share account "
        "credentials with unauthorized parties, or use automated scripts to abuse the API. "
        "Violations result in immediate account suspension pending review.")
    pdf.section("5. Service Level Agreement (Enterprise)",
        "Enterprise customers receive the following guarantees:\n"
        "- 99.9% monthly uptime (excluding scheduled maintenance)\n"
        "- Response time SLA: <1 second for AI responses\n"
        "- Support response: 1 hour for critical issues\n"
        "- Scheduled maintenance: Minimum 72 hours advance notice\n"
        "- Credits: 5% monthly fee credit per 0.1% downtime below SLA")
    pdf.section("6. Cookie Policy",
        "TechMart uses essential cookies for authentication and session management, "
        "analytics cookies to understand usage patterns (opt-in), and preference cookies "
        "to remember your settings. You can manage cookie preferences in Settings > Privacy.")
    pdf.section("7. Complaint Resolution",
        "We aim to resolve all complaints within 5 business days. Escalation path:\n"
        "1. Standard support (24-48 hours)\n"
        "2. Senior support manager (48-72 hours)\n"
        "3. Head of Customer Success (5 business days)\n"
        "4. Legal department (for formal disputes)")
    pdf.output(os.path.join(OUTPUT_DIR, "CompanyPolicies.pdf"))


def create_customer_support_guide():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("Customer Support Guide", "How to Get Help from TechMart Support")

    pdf.add_page()
    pdf.section("Support Channels",
        "TechMart offers multiple support channels to help you:\n\n"
        "- AI Chat Support: Available 24/7 through the platform chat widget\n"
        "- Email Support: support@techmart.com (response within 24 hours)\n"
        "- Phone Support: 1-800-TECHMART (Mon-Fri, 9 AM - 6 PM EST)\n"
        "- Live Chat: Available on our website during business hours\n"
        "- Community Forum: community.techmart.com\n"
        "- Documentation: docs.techmart.com")
    pdf.section("AI Chat Support",
        "Our AI-powered support system can handle most common issues instantly. "
        "The multi-agent system includes specialized agents for:\n\n"
        "- Billing questions and payment issues\n"
        "- Technical troubleshooting\n"
        "- Product information and comparisons\n"
        "- Complaint handling and escalation\n"
        "- FAQ and general inquiries\n\n"
        "Simply type your question in the chat widget and the appropriate agent will "
        "be routed to assist you.")
    pdf.section("Submitting a Ticket",
        "For complex issues that require human intervention:\n\n"
        "1. Click the 'Submit Ticket' button in the support section\n"
        "2. Select a category: Billing, Technical, Account, or General\n"
        "3. Provide a detailed description of the issue\n"
        "4. Attach relevant screenshots or files\n"
        "5. Submit the ticket\n\n"
        "You will receive a ticket number via email and can track the status in your "
        "dashboard under Support > My Tickets.")
    pdf.section("Response Times",
        "- Free tier: 48-72 hours (email only)\n"
        "- Starter: 24 hours (email)\n"
        "- Professional: 4 hours (email and chat)\n"
        "- Enterprise: 1 hour (dedicated support team)\n\n"
        "Critical system outages receive immediate attention regardless of plan tier.")
    pdf.section("Escalation Process",
        "If your issue is not resolved to your satisfaction:\n\n"
        "1. Request escalation to a senior agent in the chat\n"
        "2. If still unresolved, email escalation@techmart.com\n"
        "3. Include your ticket number and a summary of the issue\n"
        "4. A support manager will contact you within 24 hours")
    pdf.section("Self-Service Resources",
        "- Help Center: help.techmart.com\n"
        "- Video Tutorials: youtube.com/techmart\n"
        "- API Documentation: docs.techmart.com/api\n"
        "- Status Page: status.techmart.com\n"
        "- Release Notes: techmart.com/changelog")
    pdf.output(os.path.join(OUTPUT_DIR, "CustomerSupportGuide.pdf"))


def create_warranty():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("Warranty Information", "Product Warranty Terms and Claims")

    pdf.add_page()
    pdf.section("Warranty Coverage",
        "TechMart provides the following warranty on all hardware products:\n\n"
        "- Standard Warranty: 12 months from date of purchase\n"
        "- Extended Warranty: 24 months (available as add-on)\n"
        "- Enterprise Warranty: 36 months (included with Enterprise plan)")
    pdf.section("What is Covered",
        "- Manufacturing defects in materials and workmanship\n"
        "- Hardware failures under normal operating conditions\n"
        "- Firmware bugs that cause device malfunction\n"
        "- Component degradation within expected lifespan\n"
        "- Shipping damage (reported within 48 hours of delivery)")
    pdf.section("What is Not Covered",
        "- Damage caused by misuse, abuse, or negligence\n"
        "- Unauthorized modifications or repairs\n"
        "- Normal wear and tear (cosmetic damage, battery degradation)\n"
        "- Damage from power surges or electrical issues\n"
        "- Software issues caused by third-party applications\n"
        "- Products with altered or removed serial numbers")
    pdf.section("How to File a Warranty Claim",
        "1. Log in to your TechMart account\n"
        "2. Go to Support > Warranty Claims\n"
        "3. Click 'File New Claim'\n"
        "4. Select the product and describe the issue\n"
        "5. Upload photos or videos of the defect\n"
        "6. Provide proof of purchase (receipt or order number)\n"
        "7. Submit the claim\n\n"
        "Claims are typically reviewed within 2-3 business days.")
    pdf.section("Warranty Resolution Options",
        "- Repair: We will repair the defective product at no charge\n"
        "- Replacement: If repair is not possible, we will replace the product\n"
        "- Refund: If neither repair nor replacement is available, a full refund "
        "will be issued\n\n"
        "Return shipping is covered by TechMart for all valid warranty claims.")
    pdf.section("Warranty Exclusions",
        "The warranty is void if the product has been: physically damaged due to "
        "accidents, exposed to liquids or extreme conditions, used with incompatible "
        "accessories, or serviced by unauthorized technicians.")
    pdf.output(os.path.join(OUTPUT_DIR, "Warranty.pdf"))


def create_user_manual():
    pdf = KBCreator()
    pdf.alias_nb_pages()
    pdf.title_page("User Manual", "Complete Guide to Using TechMart Platform")

    pdf.add_page()
    pdf.section("Getting Started",
        "Welcome to TechMart! This guide will walk you through setting up your account "
        "and using all the features of the platform.")
    pdf.section("Account Setup",
        "1. Visit techmart.com and click 'Sign Up'\n"
        "2. Enter your email address and create a password\n"
        "3. Verify your email by clicking the link sent to your inbox\n"
        "4. Complete your profile with your name and company\n"
        "5. Choose a subscription plan (Free tier available)\n"
        "6. You're ready to start!")
    pdf.section("Dashboard Overview",
        "The main dashboard provides:\n\n"
        "- AI Chat: Access the multi-agent AI support system\n"
        "- Knowledge Base: Upload and manage your documents\n"
        "- Analytics: View conversation metrics and AI performance\n"
        "- Users: Manage team members and their roles\n"
        "- Settings: Configure your account and integrations")
    pdf.section("Using the AI Chat",
        "The AI chat system uses multiple specialized agents to provide accurate support:\n\n"
        "1. Click 'New Conversation' in the chat section\n"
        "2. Type your question or describe your issue\n"
        "3. The Intent Detection agent routes your query to the right specialist\n"
        "4. The specialist agent retrieves relevant knowledge base content\n"
        "5. The Response Validation agent ensures accuracy\n"
        "6. You receive a comprehensive, cited response\n\n"
        "You can ask about billing, technical issues, products, policies, or any "
        "general support topic.")
    pdf.section("Managing Knowledge Base",
        "Upload documents to train the AI system:\n\n"
        "1. Navigate to Knowledge Base in the sidebar\n"
        "2. Click 'Upload PDF'\n"
        "3. Select a document type (Billing, Technical, Policy, FAQ, Product)\n"
        "4. The system automatically chunks, embeds, and indexes your document\n"
        "5. The AI will use this content to answer future questions\n\n"
        "Supported formats: PDF (text-based)\n"
        "Recommended: Keep documents under 10 pages for optimal retrieval.")
    pdf.section("Analytics and Reporting",
        "Monitor your AI support performance:\n\n"
        "- Conversation volume and trends\n"
        "- AI response accuracy and confidence scores\n"
        "- Agent performance breakdown\n"
        "- Intent distribution analysis\n"
        "- Customer satisfaction ratings\n"
        "- Token usage and cost estimation")
    pdf.section("Keyboard Shortcuts",
        "- Ctrl + K: Open search\n"
        "- Ctrl + N: New conversation\n"
        "- Ctrl + Enter: Send message\n"
        "- Esc: Close modals\n"
        "- ? : Show keyboard shortcuts")
    pdf.output(os.path.join(OUTPUT_DIR, "UserManual.pdf"))


if __name__ == "__main__":
    print("Generating knowledge base documents...")
    create_billing_faq()
    print("  Created Billing_FAQ.pdf")
    create_refund_policy()
    print("  Created RefundPolicy.pdf")
    create_subscription_plans()
    print("  Created SubscriptionPlans.pdf")
    create_payment_gateway()
    print("  Created PaymentGatewayGuide.pdf")
    create_invoice_guide()
    print("  Created InvoiceGuide.pdf")
    create_billing_errors()
    print("  Created BillingErrors.pdf")
    create_company_policies()
    print("  Created CompanyPolicies.pdf")
    create_customer_support_guide()
    print("  Created CustomerSupportGuide.pdf")
    create_warranty()
    print("  Created Warranty.pdf")
    create_user_manual()
    print("  Created UserManual.pdf")
    print(f"\nAll 10 documents created in: {OUTPUT_DIR}")
