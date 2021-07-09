# -*- coding: utf-8 -*-

"""
    Infection test result reporting for RLPPTM template

    @license: MIT
"""

import base64
import datetime
import hashlib
import json
import requests
import secrets
import sys

from gluon import current, Field, IS_IN_SET, SQLFORM, \
                  DIV, H4, INPUT, TABLE, TD, TR

from s3 import S3CustomController, S3Method, \
               s3_date, s3_mark_required, s3_qrcode_represent

# =============================================================================
class TestResultRegistration(S3Method):
    """ REST Method to Register Test Results """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}
        if r.method == "register":
            output = self.register(r, **attr)
        elif r.method == "certify":
            output = self.certify(r, **attr)
        elif r.method == "cwaretry":
            output = self.cwaretry(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def register(self, r, **attr):
        """
            Register a test result

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        if r.http not in ("GET", "POST"):
            r.error(405, current.ERROR.BAD_METHOD)
        if not r.interactive:
            r.error(415, current.ERROR.BAD_FORMAT)

        T = current.T
        db = current.db
        s3db = current.s3db
        auth = current.auth

        request = current.request
        response = current.response
        s3 = response.s3

        settings = current.deployment_settings

        # Page title and intro text
        title = T("Register Test Result")

        # Get intro text from CMS
        ctable = s3db.cms_post
        ltable = s3db.cms_post_module
        join = ltable.on((ltable.post_id == ctable.id) & \
                         (ltable.module == "disease") & \
                         (ltable.resource == "case_diagnostics") & \
                         (ltable.deleted == False))

        query = (ctable.name == "TestResultRegistrationIntro") & \
                (ctable.deleted == False)
        row = db(query).select(ctable.body,
                                join = join,
                                cache = s3db.cache,
                                limitby = (0, 1),
                                ).first()
        intro = row.body if row else None

        # Instantiate Consent Tracker
        consent = s3db.auth_Consent(processing_types=["CWA_ANONYMOUS", "CWA_PERSONAL"])

        # Form Fields
        table = s3db.disease_case_diagnostics
        field = table.disease_id
        if field.writable:
            offset = 1
        else:
            field.readable = False
            offset = 0

        cwa = {"system": "RKI / Corona-Warn-App",
               "app": "Corona-Warn-App",
               }
        cwa_options = (("NO", T("Do not report")),
                       ("ANONYMOUS", T("Issue anonymous contact tracing code")),
                       ("PERSONAL", T("Issue personal test certificate")),
                       )
        formfields = [# -- Test Result --
                      table.site_id,
                      table.disease_id,
                      table.probe_date,
                      table.result,

                      # -- Report to CWA --
                      Field("report_to_cwa", "string",
                            requires = IS_IN_SET(cwa_options, sort=False, zero=""),
                            default = "NO",
                            label = T("Report test result to %(system)s") % cwa,
                            ),
                      Field("last_name",
                            label = T("Last Name"),
                            ),
                      Field("first_name",
                            label = T("First Name"),
                            ),
                      s3_date("date_of_birth",
                              label = T("Date of Birth"),
                              month_selector = True,
                              ),
                      Field("consent",
                            label = "",
                            widget = consent.widget,
                            ),
                      ]

        # Required fields
        required_fields = []

        # Subheadings
        subheadings = ((0, T("Test Result")),
                       (3 + offset, cwa["system"]),
                       )

        # Generate labels (and mark required fields in the process)
        labels, has_required = s3_mark_required(formfields,
                                                mark_required = required_fields,
                                                )
        s3.has_required = has_required

        # Form buttons
        REGISTER = T("Submit")
        buttons = [INPUT(_type = "submit",
                         _value = REGISTER,
                         ),
                   ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = "test_result",
                               record = None,
                               hidden = {"_next": request.vars._next},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = REGISTER,
                               delete_label = auth.messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Identify form for CSS & JS Validation
        form.add_class("result-register")

        # Add Subheadings
        if subheadings:
            for pos, heading in subheadings[::-1]:
                form[0].insert(pos, DIV(heading, _class="subheading"))

        # Inject scripts
        script = "/%s/static/themes/RLP/js/testresult.js" % r.application
        if script not in s3.scripts:
            s3.scripts.append(script)
        s3.jquery_ready.append("S3EnableNavigateAwayConfirm()")

        if form.accepts(request.vars,
                        current.session,
                        formname = "register",
                        onvalidation = self.validate,
                        ):

            formvars = form.vars

            # Create disease_case_diagnostics record
            testresult = {"result": formvars.get("result"),
                          }
            if "site_id" in formvars:
                testresult["site_id"] = formvars["site_id"]
            if "disease_id" in formvars:
                testresult["disease_id"] = formvars["disease_id"]
            if "probe_date" in formvars:
                testresult["probe_date"] = formvars["probe_date"]

            record_id = table.insert(**testresult)
            if not record_id:
                raise RuntimeError("Could not create testresult record")

            testresult["id"] = record_id
            # Set record owner
            auth = current.auth
            auth.s3_set_record_owner(table, record_id)
            auth.s3_make_session_owner(table, record_id)
            # Onaccept
            s3db.onaccept(table, testresult, method="create")
            response.confirmation = T("Test Result registered")

            report_to_cwa = formvars.get("report_to_cwa")
            if report_to_cwa == "NO":
                # Do not report to CWA, just forward to read view
                self.next = r.url(id=record_id, method="read")
            else:
                # Report to CWA and show test certificate
                if report_to_cwa == "ANONYMOUS":
                    processing_type = "CWA_ANONYMOUS"
                    cwa_report = CWAReport(record_id)
                elif report_to_cwa == "PERSONAL":
                    processing_type = "CWA_PERSONAL"
                    cwa_report = CWAReport(record_id,
                                           anonymous = False,
                                           first_name = formvars.get("first_name"),
                                           last_name = formvars.get("last_name"),
                                           dob = formvars.get("date_of_birth"),
                                           )
                else:
                    processing_type = cwa_report = None

                if cwa_report:
                    # Register consent
                    if processing_type:
                        cwa_report.register_consent(processing_type,
                                                    formvars.get("consent"),
                                                    )
                    # Send to CWA
                    success = cwa_report.send()
                    if success:
                        # Render the QR-code with the CWA-link
                        cwa_link = cwa_report.get_link()
                        qrcode = s3_qrcode_represent(cwa_link, show_value=False)
                        response.information = T("Result reported to %(system)s") % cwa
                        cwa_retry = False
                    else:
                        # No QR-code, prepare for retry
                        qrcode = ""
                        response.warning = T("Report to %(system)s failed") % cwa
                        cwa_retry = True

                    S3CustomController._view("RLPPTM", "certificate.html")

                    return {"title": T("Code for %(app)s") % cwa,
                            "intro": None, # TODO
                            "qrcode": qrcode,
                            "certificate": cwa_report.formatted(),
                            "cwa_data": cwa_report.data,
                            "cwa_retry": cwa_retry,
                            }
                else:
                    response.information = T("Result not reported to %(system)s") % cwa
                    self.next = r.url(id=record_id, method="read")


            return None

        elif form.errors:
            current.response.error = T("There are errors in the form, please check your input")

        # Custom View
        S3CustomController._view("RLPPTM", "testresult.html")

        return {"title": title,
                "intro": intro,
                "form": form,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def validate(form):
        """
            Validate the test result registration form
            - personal details are required for reporting to CWA by name
            - make sure the required consent option is checked
        """

        T = current.T

        formvars = form.vars

        consent = current.s3db.auth_Consent
        response = consent.parse(formvars.get("consent"))

        cwa = formvars.get("report_to_cwa")
        if cwa == "PERSONAL":
            # Personal data required
            for fn in ("first_name", "last_name", "date_of_birth"):
                if not formvars.get(fn):
                    form.errors[fn] = T("Enter a value")
            # CWA_PERSONAL consent required
            c = response.get("CWA_PERSONAL")
            if not c or not c[1]:
                form.errors.consent = T("Consent required")
        elif cwa == "ANONYMOUS":
            # CWA_ANONYMOUS consent required
            c = response.get("CWA_ANONYMOUS")
            if not c or not c[1]:
                form.errors.consent = T("Consent required")

    # -------------------------------------------------------------------------
    def certify(self, r, **attr):
        """
            Generate a test certificate (PDF) for download

            @param r: the S3Request instance
            @param attr: controller attributes
        """
        # TODO implement

        if not r.record:
            r.error(400, current.ERROR.BAD_REQUEST)
        if r.http != "POST":
            r.error(405, current.ERROR.BAD_METHOD)
        if r.representation != "pdf":
            r.error(415, current.ERROR.BAD_FORMAT)

        return "certify"

    # -------------------------------------------------------------------------
    def cwaretry(self, r, **attr):
        """
            Retry sending test result to CWA result server

            @param r: the S3Request instance
            @param attr: controller attributes
        """
        # TODO implement

        if not r.record:
            r.error(400, current.ERROR.BAD_REQUEST)
        if r.http != "POST":
            r.error(405, current.ERROR.BAD_METHOD)
        if r.representation != "json":
            r.error(415, current.ERROR.BAD_FORMAT)

        return "cwaretry"

# =============================================================================
class CWAReport(object):
    """
        CWA Report Generator
        @see: https://github.com/corona-warn-app/cwa-quicktest-onboarding/wiki/Anbindung-der-Partnersysteme
    """

    def __init__(self,
                 result_id,
                 anonymous=True,
                 first_name=None,
                 last_name=None,
                 dob=None,
                 salt=None,
                 dhash=None,
                 ):
        """
            Constructor

            @param result_id: the disease_case_diagnostics record ID
            @param anonymous: generate anonymous report
            @param first_name: first name
            @param last_name: last name
            @param doc: date of birth (str in isoformat, or datetime.date)
            @param salt: previously used salt (for retry)
            @param dhash: previously generated hash (for retry)

            @note: if not anonymous, personal data are required
        """

        db = current.db
        s3db = current.s3db

        # Lookup the result
        if result_id:
            table = s3db.disease_case_diagnostics
            query = (table.id == result_id) & \
                    (table.deleted == False)
            result = db(query).select(table.uuid,
                                      table.modified_on,
                                      table.site_id,
                                      table.disease_id,
                                      table.probe_date,
                                      table.result_date,
                                      table.result,
                                      limitby = (0, 1),
                                      ).first()
            if not result:
                raise ValueError("Test result #%s not found" % result_id)
        else:
            raise ValueError("Test result ID is required")

        # Store the test result
        self.site_id = result.site_id
        self.disease_id = result.disease_id
        self.result_date = result.result_date
        self.result = result.result

        # Determine the testid and timestamp
        testid = result.uuid
        timestamp = int(result.probe_date.replace(microsecond=0).timestamp())

        if not anonymous:
            if not all(value for value in (first_name, last_name, dob)):
                raise ValueError("Incomplete person data for personal report")
            data = {"fn": first_name,
                    "ln": last_name,
                    "dob": dob.isoformat(),
                    "timestamp": timestamp,
                    "testid": testid,
                    }
        else:
            data = {"timestamp": timestamp,
                    }

        # Add salt and hash
        data["salt"] = salt if salt else self.get_salt()
        if dhash:
            # Verify the hash
            if dhash != self.get_hash(data, anonymous=anonymous):
                raise ValueError("Invalid hash")
            data["hash"] = dhash
        else:
            data["hash"] = self.get_hash(data, anonymous=anonymous)

        self.data = data

    # -------------------------------------------------------------------------
    @staticmethod
    def get_salt():
        """
            Produce a secure 128-bit (=16 bytes) random hex token

            @returns: the token as str
        """
        return secrets.token_hex(16)

    # -------------------------------------------------------------------------
    @staticmethod
    def get_hash(data, anonymous=True):
        """
            Generate a SHA256 hash from report data string
            String formats:
            - personal : [dob]#[fn]#[ln]#[timestamp]#[testid]#[salt]
            - anonymous: [timestamp]#[salt]

            @returns: the hash as str
        """

        hashable = lambda fields: "#".join(str(data[k]) for k in fields)
        if not anonymous:
            dstr = hashable(["dob", "fn", "ln", "timestamp", "testid", "salt"])
        else:
            dstr = hashable(["timestamp", "salt"])

        return hashlib.sha256(dstr.encode("utf-8")).hexdigest().lower()

    # -------------------------------------------------------------------------
    def get_link(self):
        """
            Construct the link for QR code generation

            @returns: the link as str
        """

        # Template for CWA-link
        template = current.deployment_settings.get_custom(key="cwa_link_template")

        # Convert data to JSON
        from s3.s3xml import SEPARATORS
        data_json = json.dumps(self.data, separators=SEPARATORS)

        # Base64-encode the data JSON
        data_str = base64.urlsafe_b64encode(data_json.encode("utf-8")).decode("utf-8")

        # Generate the link
        link = template % {"data": data_str}

        return link

    # -------------------------------------------------------------------------
    def formatted(self):
        """
            Formatted version of this report to display alongside QR Code
        """

        T = current.T
        rtable = current.s3db.disease_case_diagnostics

        certificate = DIV(_class="test-certificate")
        details = TABLE()

        # Certificate Title
        field = rtable.disease_id
        if field.represent:
            disease = field.represent(self.disease_id)
            title = H4("%s %s" % (disease, T("Test Result")))
        else:
            title = H4(T("Test Result"))
        certificate.append(title)

        # Personal Details
        data = self.data
        if not any(k in data for k in ("fn", "ln", "dob")):
            details.append(TR(TD(T("Person Tested")),
                              TD(T("anonymous")),
                              ))
        else:
            labels = {"fn": T("First Name"),
                      "ln": T("Last Name"),
                      "dob": T("Date of Birth"),
                      }
            for k in ("ln", "fn", "dob"):
                value = data[k]
                details.append(TR(TD(labels.get(k)),
                               TD(value),
                               ))

        # Test Station, date and result
        field = rtable.site_id
        if field.represent:
            details.append(TR(TD(field.label),
                           TD(field.represent(self.site_id)),
                           ))
        field = rtable.probe_date
        ts = data.get("timestamp")
        if field.represent and ts:
            probe_date = datetime.datetime.fromtimestamp(ts)
            details.append(TR(TD(field.label),
                           TD(field.represent(probe_date)),
                           ))
        field = rtable.result
        if field.represent:
            details.append(TR(TD(field.label),
                           TD(field.represent(self.result)),
                           ))

        certificate.append(details)

        return certificate

    # -------------------------------------------------------------------------
    def register_consent(self, processing_type, response):
        """
            Register consent assertion using the current hash as reference

            @param processing type: the data processing type for which
                                    consent is required
            @param response: the consent response
        """

        data = self.data

        dhash = data.get("hash")
        if not dhash:
            raise ValueError("Missing context hash")

        consent = current.s3db.auth_Consent
        consent.assert_consent(dhash, processing_type, response)

    # -------------------------------------------------------------------------
    def send(self):
        """
            Send the CWA Report to the server;
            see also: https://github.com/corona-warn-app/cwa-quicktest-onboarding/blob/master/api/quicktest-openapi.json

            @returns: True|False whether successful
        """

        # Encode the result
        results = {"NEG": 6, "POS": 7, "INC": 8}
        result = results.get(self.result)
        if not result:
            current.log.error("CWAReport: invalid test result %s" % self.result)
            return False

        # Build the QuickTestResult JSON structure
        data = self.data
        testresult = {"id": data.get("hash"),
                      "sc": data.get("timestamp"),
                      "result": result,
                      }

        # The CWA server URL
        settings = current.deployment_settings
        server_url = settings.get_custom("cwa_server_url")
        if not server_url:
            raise RuntimeError("No CWA server URL configured")

        # The client credentials to access the server
        folder = current.request.folder
        cert = settings.get_custom("cwa_client_certificate")
        key = settings.get_custom("cwa_certificate_key")
        if not cert or not key:
            raise RuntimeError("No CWA client credentials configured")
        cert = "%s/%s" % (folder, cert)
        key = "%s/%s" % (folder, key)

        # The certificate chain to verify the server identity
        verify = settings.get_custom("cwa_server_ca")
        if verify:
            # Use the specified CA Certificate to verify server identity
            verify = "%s/%s" % (current.request.folder, verify)
        else:
            # Use python-certifi (=> make sure the latest version is installed)
            verify = True

        # POST to server
        try:
            sr = requests.post(server_url,
                               # Send a QuickTestResultList
                               json = {"testResults": [testresult]},
                               cert = (cert, key),
                               verify = verify,
                               )
        except Exception:
            # Local error
            error = sys.exc_info()[1]
            current.log.error("CWAReport: transmission to CWA server failed (local error: %s)" % error)
            return False

        # Check return code (should be 204, but 202/200 would also be good news)
        if sr.status_code not in (204, 202, 200):
            # Remote error
            current.log.error("CWAReport: transmission to CWA server failed, status code %s" % sr.status_code)
            return False

        # Success
        return True

# END =========================================================================
