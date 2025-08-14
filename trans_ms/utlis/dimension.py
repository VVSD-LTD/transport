# Copyright (c) 2021, Aakvatech Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def set_dimension(src_doc, tr_doc, src_child=None, tr_child=None):
    try:
        settings = frappe.get_doc("Transport Settings", "Transport Settings")
    except Exception as e:
        frappe.log_error(f"Transport Settings missing or error: {e}", "set_dimension")
        return

    if not getattr(settings, "accounting_dimension", []):
        frappe.log_error("No accounting dimensions found", "set_dimension")
        return

    for dim in settings.accounting_dimension:
        try:
            # Check if this dimension applies to the current document types
            # Handle case when tr_doc is None (for child-only operations)
            if tr_doc and (dim.source_doctype != src_doc.doctype or dim.target_doctype != tr_doc.doctype):
                continue
            elif not tr_doc and dim.target_type == "Main":
                # Skip main document dimensions when tr_doc is None
                continue

            value = None
            source_info = ""

            # Get the source value
            if dim.source_type == "Field":
                value = src_doc.get(dim.source_field_name)
                source_info = f"From Field: {dim.source_field_name}"
            elif dim.source_type == "Value":
                value = dim.value
                source_info = f"From Static Value"
            elif dim.source_type == "Child":
                # For child source type, we need to find the value from the child table
                if src_child:
                    # Use the provided src_child (when processing individual items)
                    value = src_child.get(dim.child_field_name) if dim.child_field_name else None
                    source_info = f"From Child Field: {dim.child_field_name}"
                elif hasattr(src_doc, dim.source_field_name):
                    # Look in the source document's child table
                    child_table = getattr(src_doc, dim.source_field_name, [])
                    if child_table and dim.child_field_name:
                        # Get the value from the first child row (you might need to adjust this logic)
                        value = child_table[0].get(dim.child_field_name) if len(child_table) > 0 else None
                        source_info = f"From Child Table {dim.source_field_name}, Field: {dim.child_field_name}"
                    else:
                        value = None
                        source_info = f"Child table {dim.source_field_name} empty or missing field"
                else:
                    value = None
                    source_info = f"Source child table {dim.source_field_name} not found"
            else:
                source_info = f"Unknown source type: {dim.source_type}"
                value = None

            # Set the target value
            target_info = ""
            
            if dim.target_type == "Main" and tr_doc:
                # Set dimension on the main document
                if hasattr(tr_doc, dim.target_field_name):
                    setattr(tr_doc, dim.target_field_name, value)
                    target_info = f"Set {dim.target_field_name} in Main Doc"
                else:
                    target_info = f"Skipped: Main doc missing field {dim.target_field_name}"
                    
            elif dim.target_type == "Child":
                # Handle child table dimensions
                if tr_child is not None:
                    # We have a specific child row to update
                    target_field = dim.target_child_field_name
                    if isinstance(tr_child, dict):
                        tr_child[target_field] = value
                    else:
                        setattr(tr_child, target_field, value)
                    target_info = f"Set {target_field} in Child Row"
                    
                elif hasattr(tr_doc, dim.target_field_name):
                    # No specific child row, but we can update all rows in the child table
                    child_table = getattr(tr_doc, dim.target_field_name, [])
                    if child_table:
                        for child_row in child_table:
                            if isinstance(child_row, dict):
                                child_row[dim.target_child_field_name] = value
                            else:
                                setattr(child_row, dim.target_child_field_name, value)
                        target_info = f"Set {dim.target_child_field_name} in all {dim.target_field_name} rows"
                    else:
                        target_info = f"Skipped: No rows in {dim.target_field_name} table"
                else:
                    target_info = f"Skipped: target_type=Child, no tr_child provided and no {dim.target_field_name} table found"
            else:
                target_info = f"Skipped: Unknown target_type={dim.target_type}"

            # Log the mapping attempt
            # frappe.log_error(
            #     f"""Dimension: {dim.dimension_name}
            #     Source DocType: {dim.source_doctype}
            #     Target DocType: {dim.target_doctype}
            #     Source: {source_info}
            #     Target: {target_info}
            #     Value: {value}""",
            #     "set_dimension mapping"
            # )

        except Exception as e:
            frappe.log_error(f"Error processing dimension {dim.dimension_name}: {str(e)}\nTraceback: {frappe.get_traceback()}", "set_dimension")


# def set_dimension(src_doc, tr_doc, src_child=None, tr_child=None):
#     set = frappe.get_cached_doc("Transport Settings", "Transport Settings")
#     if len(set.accounting_dimension) == 0:
#         return
#     for dim in set.accounting_dimension:
#         if (
#             dim.source_doctype == src_doc.doctype
#             and dim.target_doctype == tr_doc.doctype
#         ):
#             value = None

#             if dim.source_type == "Field":
#                 value = src_doc.get(dim.source_field_name)
#             elif dim.source_type == "Value":
#                 value = dim.value
#             elif dim.source_type == "Child" and src_child:
#                 value = src_child.get(dim.child_field_name)
            
#             if dim.target_type == "Main":
#                 setattr(tr_doc, dim.target_field_name, value)
#             elif dim.target_type == "Child" and tr_child:
#                 setattr(tr_child, dim.target_child_field_name, value)