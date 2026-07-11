"""Versioned counsel-review legal drafts and acceptance helpers."""
import hashlib
from .models import LegalAcceptance

DOCUMENTS={
'TERMS':{'version':'2026-07-11','title':'Platform Terms and Conditions','summary':'Rules for accounts, marketplace purchases, payments, delivery, disputes, and acceptable use.'},
'PRIVACY':{'version':'2026-07-11','title':'Privacy Notice','summary':'How Optimistic collects, uses, shares, secures, retains, and responds to rights requests for personal data.'},
'SELLER_TERMS':{'version':'2026-07-11','title':'Seller Marketplace Terms','summary':'Seller identity, listing accuracy, stock, fulfillment, fees, taxes, prohibited goods, returns, payouts, and enforcement obligations.'},
}
for value in DOCUMENTS.values(): value['content_hash']=hashlib.sha256((value['title']+'|'+value['version']+'|'+value['summary']).encode()).hexdigest()

def record_acceptance(*,user,document,request):
    definition=DOCUMENTS[document]
    forwarded=request.META.get('HTTP_X_FORWARDED_FOR','').split(',')[0].strip()
    return LegalAcceptance.objects.get_or_create(user=user,document=document,version=definition['version'],defaults={'content_hash':definition['content_hash'],'ip_address':forwarded or request.META.get('REMOTE_ADDR') or None,'user_agent':request.META.get('HTTP_USER_AGENT','')[:500]})

def has_current_acceptance(user,document):
    return LegalAcceptance.objects.filter(user=user,document=document,version=DOCUMENTS[document]['version']).exists()
