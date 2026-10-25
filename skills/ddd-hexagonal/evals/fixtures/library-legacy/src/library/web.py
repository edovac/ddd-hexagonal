from flask import Flask, jsonify, request

from library import catalog, loans, members
from library.db import connect

app = Flask(__name__)

MAX_LOANS = 5  # front desk limit


@app.post("/members")
def register_member():
    body = request.get_json()
    with connect() as conn:
        try:
            member_id = members.register(conn, body["name"], body["email"], body.get("kind", "adult"))
        except members.MemberError as e:
            return jsonify(error=str(e)), 400
    return jsonify(id=member_id), 201


@app.post("/members/<int:member_id>/payments")
def pay(member_id):
    with connect() as conn:
        try:
            members.pay_fees(conn, member_id, float(request.get_json()["amount"]))
        except members.MemberError as e:
            return jsonify(error=str(e)), 400
    return "", 204


@app.post("/books")
def add_book():
    body = request.get_json()
    with connect() as conn:
        try:
            book_id = catalog.add_book(conn, body["isbn"], body["title"], body.get("reference_only", False))
        except catalog.CatalogError as e:
            return jsonify(error=str(e)), 400
    return jsonify(id=book_id), 201


@app.post("/loans")
def lend():
    body = request.get_json()
    with connect() as conn:
        if len(loans.open_loans(conn, body["member_id"])) >= MAX_LOANS:
            return jsonify(error="Too many books on loan"), 409
        try:
            loan_id = loans.lend(conn, body["member_id"], body["book_id"])
        except loans.LoanError as e:
            return jsonify(error=str(e)), 409
    return jsonify(id=loan_id), 201


@app.post("/loans/<int:loan_id>/renewal")
def renew(loan_id):
    with connect() as conn:
        try:
            loans.renew(conn, loan_id)
        except loans.LoanError as e:
            return jsonify(error=str(e)), 409
    return "", 204


@app.post("/loans/<int:loan_id>/return")
def give_back(loan_id):
    with connect() as conn:
        fee = loans.give_back(conn, loan_id)
    return jsonify(fee=fee), 200
