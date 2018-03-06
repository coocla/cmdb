#coding:utf-8
import logging
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import JsonResponse, Http404
from django.core.urlresolvers import reverse
from django.views.generic import View

from asset import dnspod
from asset.models import (CDNCompany, AccelerateCDN, ResolveAudit)
from asset.forms import (CDNCompanyForm, AccelerateCDNForm, DomainForm, RegisterDomain, DNSPodForm)

logger = logging.getLogger(__name__)

class CDNCompanyCreate(View):
    def get(self, req):
        form = CDNCompanyForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("cdncompany_create")}))

    def post(self, req):
        form = CDNCompanyForm(req.POST)
        if form.is_valid():
            cdncompany = form.save()
            return JsonResponse({"success": True, "msg": u"CDN厂商创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class CDNCompanyUpdate(View):
    def get(self, req, cdn_uuid):
        form = CDNCompanyForm(instance=CDNCompany.objects.get(pk=cdn_uuid))
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("cdncompany_update", kwargs={"cdn_uuid":cdn_uuid})}))

    def post(self, req, cdn_uuid):
        form = CDNCompanyForm(req.POST, instance=CDNCompany.objects.get(pk=cdn_uuid))
        if form.is_valid():
            cdncompany = form.save()
            return JsonResponse({"success": True, "msg": u"CDN厂商更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class AccelerateCreate(View):
    def get(self, req):
        form = AccelerateCDNForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("accelerate_create")}))

    def post(self, req):
        form = AccelerateCDNForm(req.POST)
        if form.is_valid():
            accelerate = form.save()
            return JsonResponse({"success": True, "msg": u"CDN域名创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class AccelerateUpdate(View):
    def get(self, req, accelerate_uuid):
        form = AccelerateCDNForm(instance=AccelerateCDN.objects.get(pk=accelerate_uuid))
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("accelerate_update", kwargs={"accelerate_uuid":accelerate_uuid})}))

    def post(self, req, accelerate_uuid):
        form = AccelerateCDNForm(req.POST, instance=AccelerateCDN.objects.get(pk=accelerate_uuid))
        if form.is_valid():
            accelerate = form.save()
            return JsonResponse({"success": True, "msg": u"CDN域名创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class DomainCreate(View):
    def get(self, req):
        form = DomainForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("domain_create")}))


    def post(self, req):
        form = DomainForm(req.POST)
        if form.is_valid():
            domain = form.save()
            return JsonResponse({"success": True, "msg": u"域名记录创建成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class DomainUpdate(View):
    def get(self, req, domain_uuid):
        form = DomainForm(instance=RegisterDomain.objects.get(pk=domain_uuid))
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("domain_update", kwargs={"domain_uuid":domain_uuid})}))

    def post(self, req, domain_uuid):
        form = AccelerateCDNForm(req.POST, instance=RegisterDomain.objects.get(pk=domain_uuid))
        if form.is_valid():
            domain = form.save()
            return JsonResponse({"success": True, "msg": u"域名记录更新成功!"})
        return JsonResponse({"success": False, "msg": form.errors})

class ResolverList(View):
    def get(self, req):
        record = req.GET.get("domain")
        if record.count(".") < 2:
            return JsonResponse({"results": []})
        domain = ".".join(record.split(".")[-2:])
        sub_domain = ".".join(record.split(".")[:-2])
        try:
            result = dnspod.RecordList(domain, sub_domain)
            if dnspod.veritify(result)[0]:
                results = []
                for r in result["records"]:
                    results.append({
                        "record_id": r["id"],
                        "record_name": r["name"],
                        "record_line": r["line"],
                        "record_type": r["type"],
                        "record_ttl": r["ttl"],
                        "status": r["enabled"],
                        "value": r["value"],
                        "domain_id": result["domain"]["id"],
                        "domain_name": result["domain"]["name"],
                        "updated_at": r["updated_on"],
                    })
                return JsonResponse({"results": results, "count": result["info"]["record_total"]})
        except:
            return JsonResponse({"results": [], "count": 0})
        return JsonResponse({"results": [], "count": 0})


class ResolverCreate(View):
    def get(self, req):
        form = DNSPodForm()
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("resolver_create")}))

    def post(self, req):
        form = DNSPodForm(req.POST)
        if form.is_valid():
            try:
                rr = dnspod.RecordCreate(**form.cleaned_data)
                success, msg = dnspod.veritify(rr)
                if success:
                    ra = ResolveAudit(userid=req.user.uuid, username=req.user.name, \
                            record=form.cleaned_data["record"], \
                            description=u"添加 %(record_type)s 记录 %(record_line)s 线路 值 %(value)s" % form.cleaned_data)
                    ra.save()
            except Exception,e:
                logger.error(e, exc_info=True)
                success = False
                msg = u"内部错误"
            return JsonResponse({"success": success, "msg": msg})
        return JsonResponse({"success": False, "msg": form.errors})

class ResolverUpdate(View):
    def get(self, req, domain, record_id):
        try:
            result = dnspod.RecordInfo(domain, record_id)
            if dnspod.veritify(result)[0]:
                data = {"record": "%s.%s" % (result["record"]["sub_domain"], result["domain"]["name"]),
                        "value": result["record"]["value"],
                        "record_line": result["record"]["record_line"],
                        "record_type": result["record"]["record_type"]}
            else:
                raise Http404
        except:
            raise Http404

        form = DNSPodForm(initial=data)
        return render_to_response('common/forms.html', context_instance=RequestContext(req, \
                {"form": form, "url": reverse("resolver_create")}))

    def post(self, req, domain, record_id):
        form = DNSPodForm(req.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data.copy()
                data["record_id"] = record_id
                success, msg = dnspod.RecordModify(**data)
                if success:
                    ra = ResolveAudit(userid=req.user.uuid, username=req.user.name, \
                            record=form.cleaned_data["record"], \
                            description=u"更新 %(record_type)s 记录 %(record_line)s 线路 值 %(value)s" % form.cleaned_data)
                    ra.save()
            except Exception,e:
                logger.error(e, exc_info=True)
                success = False
                msg = u"内部错误"
            return JsonResponse({"success": success, "msg": msg})
        return JsonResponse({"success": False, "msg": form.errors})
