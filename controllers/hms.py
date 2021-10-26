# -*- coding: utf-8 -*-

"""
    HMS Hospital Status Assessment and Request Management System
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
#def s3_menu_postp():
#    # @todo: rewrite this for new framework
#    if len(request.args) > 0 and request.args[0].isdigit():
#        newreq = dict(from_record="hms_hospital.%s" % request.args[0],
#                      from_fields="hospital_id$id")
#        #selreq = {"req.hospital_id":request.args[0]}
#    else:
#        newreq = dict()
#    selreq = {"req.hospital_id__ne":"NONE"}
#    menu_selected = []
#    hospital_id = s3base.s3_get_last_record_id("hms_hospital")
#    if hospital_id:
#        hospital = s3db.hms_hospital
#        query = (hospital.id == hospital_id)
#        record = db(query).select(hospital.id,
#                                  hospital.name,
#                                  limitby=(0, 1)).first()
#        if record:
#            name = record.name
#            menu_selected.append(["%s: %s" % (T("Hospital"), name), False,
#                                 URL(f="hospital",
#                                     args=[record.id])])
#    if menu_selected:
#        menu_selected = [T("Open recent"), True, None, menu_selected]
#        response.menu_options.append(menu_selected)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    from s3db.cms import cms_index
    return cms_index(c, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the Hospitals Map
    s3_redirect_default(URL(f = "hospital",
                            args = ["map"],
                            ))

# =============================================================================
def hospital():
    """
        Main REST controller for Hospitals
    """

    # Custom Method to Assign HRs
    from s3db.hrm import hrm_AssignMethod
    s3db.set_method("hms", "hospital",
                    method = "assign",
                    action = hrm_AssignMethod(component = "human_resource_site"),
                    )

    # Pre-processor
    def prep(r):
        # Function to call for all Site Instance Types
        from s3db.org import org_site_prep
        org_site_prep(r)

        if r.interactive:
            if r.component:
                cname = r.component_name
                if cname == "status":
                    table = db.hms_status
                    table.facility_status.comment = DIV(_class = "tooltip",
                                                        _title = "%s|%s" % (T("Facility Status"),
                                                                            T("Status of the facility."),
                                                                            ),
                                                        )
                    table.facility_operations.comment = DIV(_class = "tooltip",
                                                            _title = "%s|%s" % (T("Facility Operations"),
                                                                                T("Overall status of the facility operations."),
                                                                                ),
                                                            )
                    table.clinical_status.comment = DIV(_class = "tooltip",
                                                        _title = "%s|%s" % (T("Clinical Status"),
                                                                            T("Status of the clinical departments."),
                                                                            ),
                                                        )
                    table.clinical_operations.comment = DIV(_class = "tooltip",
                                                            _title = "%s|%s" % (T("Clinical Operations"),
                                                                                T("Overall status of the clinical operations."),
                                                                                ),
                                                            )
                    table.ems_status.comment = DIV(_class = "tooltip",
                                                   _title = "%s|%s" % (T("Emergency Medical Services"),
                                                                       T("Status of operations/availability of emergency medical services at this facility."),
                                                                       ),
                                                   )
                    table.ems_reason.comment = DIV(_class = "tooltip",
                                                   _title = "%s|%s" % (T("EMS Status Reasons"),
                                                                       T("Report the contributing factors for the current EMS status."),
                                                                       ),
                                                   )
                    table.or_status.comment = DIV(_class = "tooltip",
                                                  _title = "%s|%s" % (T("OR Status"),
                                                                      T("Status of the operating rooms of this facility."),
                                                                      ),
                                                  )
                    table.or_reason.comment = DIV(_class = "tooltip",
                                                  _title = "%s|%s" % (T("OR Status Reason"),
                                                                      T("Report the contributing factors for the current OR status."),
                                                                      ),
                                                  )
                    table.morgue_status.comment = DIV(_class = "tooltip",
                                                      _title = "%s|%s" % (T("Morgue Status"),
                                                                          T("Status of morgue capacity."),
                                                                          ),
                                                      )
                    table.morgue_units.comment = DIV(_class = "tooltip",
                                                     _title = "%s|%s" % (T("Morgue Units Available"),
                                                                         T("Number of vacant/available units to which victims can be transported immediately."),
                                                                         ),
                                                     )
                    table.security_status.comment = DIV(_class = "tooltip",
                                                        _title = "%s|%s" % (T("Security Status"),
                                                                            T("Status of security procedures/access restrictions for the facility."),
                                                                            ),
                                                        )
                    table.staffing.comment = DIV(_class = "tooltip",
                                                 _title = "%s|%s" % (T("Staffing Level"),
                                                                     T("Current staffing level at the facility."),
                                                                     ),
                                                 )
                    table.access_status.comment = DIV(_class = "tooltip",
                                                      _title = "%s|%s" % (T("Road Conditions"),
                                                                          T("Describe the condition of the roads from/to the facility."),
                                                                          ),
                                                      )

                elif cname == "bed_capacity":
                    table = db.hms_bed_capacity
                    table.bed_type.comment = DIV(_class = "tooltip",
                                                 _title = "%s|%s" % (T("Bed Type"),
                                                                     T("Specify the bed type of this unit."),
                                                                     ),
                                                 )
                    table.beds_baseline.comment = DIV(_class = "tooltip",
                                                      _title = "%s|%s" % (T("Baseline Number of Beds"),
                                                                          T("Baseline number of beds of that type in this unit."),
                                                                          ),
                                                      )
                    table.beds_available.comment = DIV(_class = "tooltip",
                                                       _title = "%s|%s" % (T("Available Beds"),
                                                                           T("Number of available/vacant beds of that type in this unit at the time of reporting."),
                                                                           ),
                                                       )
                    table.beds_add24.comment = DIV(_class = "tooltip",
                                                   _title = "%s|%s" % (T("Additional Beds / 24hrs"),
                                                                       T("Number of additional beds of that type expected to become available in this unit within the next 24 hours."),
                                                                       ),
                                                   )
                elif cname == "activity":
                    table = db.hms_activity
                    table.date.comment = DIV(_class = "tooltip",
                                             _title = "%s|%s" % (T("Date & Time"),
                                                                 T("Date and time this report relates to."),
                                                                 ),
                                             )
                    table.patients.comment = DIV(_class = "tooltip",
                                                 _title = "%s|%s" % (T("Patients"),
                                                                     T("Number of in-patients at the time of reporting."),
                                                                     ),
                                                 )
                    table.admissions24.comment = DIV(_class = "tooltip",
                                                     _title = "%s|%s" % (T("Admissions/24hrs"),
                                                                         T("Number of newly admitted patients during the past 24 hours."),
                                                                         ),
                                                     )

                    table.discharges24.comment = DIV(_class = "tooltip",
                                                     _title = "%s|%s" % (T("Discharges/24hrs"),
                                                                         T("Number of discharged patients during the past 24 hours."),
                                                                         ),
                                                     )
                    table.deaths24.comment = DIV(_class = "tooltip",
                                                 _title = "%s|%s" % (T("Deaths/24hrs"),
                                                                     T("Number of deaths during the past 24 hours."),
                                                                     ),
                                                 )

                elif cname == "contact":
                    table = db.hms_contact
                    table.title.comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("Title"),
                                                                  T("The Role this person plays within this hospital."),
                                                                  ),
                                              )

                elif cname == "image":
                    table = s3db.doc_image
                    table.location_id.readable = table.location_id.writable = False
                    table.organisation_id.readable = table.organisation_id.writable = False
                    table.person_id.readable = table.person_id.writable = False

                elif cname == "ctc":
                    table = db.hms_ctc
                    table.ctc.comment = DIV(_class = "tooltip",
                                            _title = "%s|%s" % (T("Cholera Treatment Center"),
                                                                T("Does this facility provide a cholera treatment center?"),
                                                                ),
                                            )
                    table.number_of_patients.comment = DIV(_class = "tooltip",
                                                           _title = "%s|%s" % (T("Current number of patients"),
                                                                               T("How many patients with the disease are currently hospitalized at this facility?"),
                                                                               ),
                                                           )
                    table.cases_24.comment = DIV(_class = "tooltip",
                                                 _title = "%s|%s" % (T("New cases in the past 24h"),
                                                                     T("How many new cases have been admitted to this facility in the past 24h?"),
                                                                     ),
                                                 )
                    table.deaths_24.comment = DIV(_class = "tooltip",
                                                  _title = "%s|%s" % (T("Deaths in the past 24h"),
                                                                      T("How many of the patients with the disease died in the past 24h at this facility?"),
                                                                      ),
                                                  )
                    table.icaths_available.comment = DIV(_class = "tooltip",
                                                         _title = "%s|%s" % (T("Infusion catheters available"),
                                                                             T("Specify the number of available sets"),
                                                                             ),
                                                         )

                    table.icaths_needed_24.comment = DIV(_class = "tooltip",
                                                         _title = "%s|%s" % (T("Infusion catheters need per 24h"),
                                                                             T("Specify the number of sets needed per 24h"),
                                                                             ),
                                                         )

                    table.infusions_available.comment = DIV(_class = "tooltip",
                                                            _title = "%s|%s" % (T("Infusions available"),
                                                                                T("Specify the number of available units (litres) of Ringer-Lactate or equivalent solutions"),
                                                                                ),
                                                            )
                    table.infusions_needed_24.comment = DIV(_class = "tooltip",
                                                            _title = "%s|%s" % (T("Infusions needed per 24h"),
                                                                                T("Specify the number of units (litres) of Ringer-Lactate or equivalent solutions needed per 24h"),
                                                                                ),
                                                            )
                    table.antibiotics_available.comment = DIV(_class = "tooltip",
                                                              _title = "%s|%s" % (T("Antibiotics available"),
                                                                                  T("Specify the number of available units (adult doses)"),
                                                                                  ),
                                                              )
                    table.antibiotics_needed_24.comment = DIV(_class = "tooltip",
                                                              _title = "%s|%s" % (T("Antibiotics needed per 24h"),
                                                                                  T("Specify the number of units (adult doses) needed per 24h"),
                                                                                  ),
                                                              )
                    table.problem_types.comment = DIV(_class = "tooltip",
                                                      _title = "%s|%s" % (T("Current problems, categories"),
                                                                          T("Select all that apply"),
                                                                          ),
                                                      )
                    table.problem_details.comment = DIV(_class = "tooltip",
                                                        _title = "%s|%s" % (T("Current problems, details"),
                                                                            T("Please specify any problems and obstacles with the proper handling of the disease, in detail (in numbers, where appropriate). You may also add suggestions the situation could be improved."),
                                                                            ),
                                                        )
            else:
                # No Component
                from s3 import S3LocationFilter, S3OptionsFilter, S3RangeFilter, S3TextFilter
                stable = s3db.hms_status
                filter_widgets = [
                        S3TextFilter(["name",
                                      "code",
                                      "comments",
                                      "organisation_id$name",
                                      "organisation_id$acronym",
                                      "location_id$name",
                                      "location_id$L1",
                                      "location_id$L2",
                                      ],
                                     label = T("Name"),
                                     _class = "filter-search",
                                     ),
                        S3OptionsFilter("facility_type",
                                        label = T("Type"),
                                        #hidden = True,
                                        ),
                        S3LocationFilter("location_id",
                                         label = T("Location"),
                                         levels = ("L0", "L1", "L2"),
                                         #hidden = True,
                                         ),
                        S3OptionsFilter("status.facility_status",
                                        label = T("Status"),
                                        options = stable.facility_status.represent.options,
                                        #represent = "%(name)s",
                                        #hidden = True,
                                        ),
                        S3OptionsFilter("status.power_supply_type",
                                        label = T("Power"),
                                        options = stable.power_supply_type.represent.options,
                                        #represent = "%(name)s",
                                        #hidden = True,
                                        ),
                        S3OptionsFilter("bed_capacity.bed_type",
                                        label = T("Bed Type"),
                                        options = s3db.hms_bed_capacity.bed_type.represent.options,
                                        #represent = "%(name)s",
                                        #hidden = True,
                                        ),
                        S3RangeFilter("total_beds",
                                      label = T("Total Beds"),
                                      #represent = "%(name)s",
                                      #hidden = True,
                                      ),
                        ]

                s3db.configure("hms_hospital",
                               filter_widgets = filter_widgets,
                               )

                s3.formats["have"] = r.url() # .have added by JS
                # Add comments
                table = r.table
                table.gov_uuid.comment = DIV(_class = "tooltip",
                                             _title = "%s|%s" % (T("Government UID"),
                                                                 T("The Unique Identifier (UUID) as assigned to this facility by the government."),
                                                                 ),
                                             )
                table.total_beds.comment = DIV(_class = "tooltip",
                                               _title = "%s|%s" % (T("Total Beds"),
                                                                   T("Total number of beds in this facility. Automatically updated from daily reports."),
                                                                   ),
                                               )
                table.available_beds.comment = DIV(_class = "tooltip",
                                                   _title = "%s|%s" % (T("Available Beds"),
                                                                       T("Number of vacant/available beds in this facility. Automatically updated from daily reports."),
                                                                       ),
                                                   )

        elif r.representation == "plain":
            # Duplicates info in the other fields
            r.table.location_id.readable = False

        return True
    s3.prep = prep

    from s3db.hms import hms_hospital_rheader
    return s3_rest_controller(rheader = hms_hospital_rheader)

# =============================================================================
def person():
    """
        RESTful CRUD controller for Hospital Contacts (e.g. Doctors)
    """

    s3.filter = (FS("hms_contact.hospital_id") != None)

    from s3db.pr import pr_Contacts
    s3db.set_method("pr", "person",
                    method = "contacts",
                    action = pr_Contacts,
                    )

    # @ToDo: Move to Template
    s3.crud_strings["pr_person"] = Storage(
        label_create = T("Create Medical Personnel"),
        title_display = T("Medical Personnel Details"),
        title_list = T("Medical Personnel"),
        title_update = T("Edit Medical Personnel"),
        label_list_button = T("List Medical Personnel"),
        label_delete_button = T("Delete Medical Personnel"),
        msg_record_created = T("Medical Personnel added"),
        msg_record_modified = T("Medical Personnel updated"),
        msg_record_deleted = T("Medical Personnel deleted"),
        msg_list_empty = T("No Medical Personnel currently defined"),
        )

    list_fields = ["first_name",
                   "middle_name",
                   "last_name",
                   (T("Qualifications"), "competency.skill_id"),
                   "hms_contact.hospital_id",
                   ]

    from s3 import S3SQLCustomForm, S3SQLInlineComponent

    crud_form = S3SQLCustomForm("first_name",
                                "middle_name",
                                "last_name",
                                "hms_contact.hospital_id",
                                S3SQLInlineComponent("competency",
                                                     label = T("Qualifications"),
                                                     fields = [("", "skill_id"),
                                                               ]
                                                     ),
                                )

    s3db.configure("pr_person",
                   crud_form = crud_form,
                   list_fields = list_fields,
                   )

    def rheader(r):
        if r.representation != "html":
            # RHeaders only used in interactive views
            return None
        record = r.record
        if record is None:
            # List or Create form: rheader makes no sense here
            return None

        tabs = [(T("Person Details"), None),
                (T("Contacts"), "contacts"),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)

        from s3 import s3_fullname

        #hospital_field = r.table.hospital_id

        rheader = DIV(TABLE(TR(TH("%s: " % T("Name")),
                               s3_fullname(record),
                               ),
                            #TR(TH("%s: " % hospital_field.label),
                            #   hospital_field.represent(record.hospital_id),
                            #   ),
                            ),
                      rheader_tabs,
                      )
        return rheader

    return s3_rest_controller("pr", "person",
                              rheader = rheader,
                              )

# =============================================================================
def pharmacy():
    """
        RESTful CRUD controller for Pharmacies
    """

    # Pre-processor
    def prep(r):
        # Function to call for all Site Instance Types
        from s3db.org import org_site_prep
        org_site_prep(r)

        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def incoming():
    """
        Incoming Shipments for Sites

        Used from Requests rheader when looking at Transport Status
    """

    # @ToDo: Create this function!
    return s3db.inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    from s3db.inv import inv_req_match
    return inv_req_match()

# END =========================================================================

