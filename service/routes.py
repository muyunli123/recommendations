######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Recommendations Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Recommendations
"""
# pylint: disable=unused-import
# import secrets
from flask_restx import Resource, fields, reqparse, inputs  # noqa: F401
from flask import jsonify, request, abort
from flask import current_app as app  # Import Flask application
from werkzeug.exceptions import BadRequest
from service.models import Recommendations
from service.common import status  # HTTP Status Codes
from . import api  # pylint: disable=cyclic-import


# from sqlalchemy.exc import SQLAlchemyError
# from service.models import DataValidationError


######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    app.logger.info("Health check endpoint called")
    return jsonify({"status": "OK"}), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for Root URL")
    return app.send_static_file("index.html")


# Define the model so that the docs reflect what can be sent
create_model = api.model(
    "Recommendations",
    {
        "product_id": fields.Integer(
            required=True, description="The product id of the Recommendation"
        ),
        "recommended_id": fields.Integer(
            required=True,
            description="The recommended product id of the Recommendation",
        ),
        "recommendation_type": fields.String(
            required=True,
            description="The type of Recommendation (e.g., cross-sell, up-sell, accessory, etc.)",
        ),
        "status": fields.String(
            required=True,
            description="The status of Recommendation (e.g., active, draft, expired, etc.)",
        ),
        "like": fields.Integer(
            required=False, description="Number of likes (default: 0)"
        ),  # Add this
        "dislike": fields.Integer(
            required=False, description="Number of dislikes (default: 0)"
        ),  # Add this
        "created_at": fields.DateTime(required=False, description="Creation timestamp"),
        "last_updated": fields.DateTime(
            required=False, description="Last updated timestamp"
        ),
        # pylint: disable=protected-access
    },
)

recommendation_model = api.inherit(
    "RecommendationModel",
    create_model,
    {
        "id": fields.Integer(
            readOnly=True, description="The unique id assigned internally by service"
        ),
    },
)

# query string arguments
recommendation_args = reqparse.RequestParser()
recommendation_args.add_argument(
    "product_id",
    type=int,
    location="args",
    required=False,
    help="List Recommendations by product id",
)
recommendation_args.add_argument(
    "recommended_id",
    type=int,
    location="args",
    required=False,
    help="List Recommendations by recommended id",
)
recommendation_args.add_argument(
    "recommendation_type",
    type=str,
    location="args",
    required=False,
    help="List Recommendations by type",
)
recommendation_args.add_argument(
    "status",
    type=str,
    location="args",
    required=False,
    help="List Recommendations by status",
)
recommendation_args.add_argument(
    "page", type=int, location="args", required=False, help="Pagination page number"
)
recommendation_args.add_argument(
    "limit", type=int, location="args", required=False, help="Pagination limit per page"
)
recommendation_args.add_argument(
    "sort_by", type=str, location="args", required=False, help="Sort by field"
)
recommendation_args.add_argument(
    "order", type=str, location="args", required=False, help="Sort order (asc or desc)"
)


######################################################################
# Function to generate a random API key (good for testing)
######################################################################
# def generate_apikey():
#     """Helper function used when testing API keys"""
#     return secrets.token_hex(16)


######################################################################
#  PATH: /recommendations/{id}
######################################################################
@api.route("/recommendations/<int:recommendation_id>")
@api.param("recommendation_id", "The Recommendation identifier")
class RecommendationResource(Resource):
    """
    RecommendationResource class

    Allows the manipulation of a single Recommendation
    GET /recommendation{id} - Returns a Recommendation with the id
    PUT /recommendation{id} - Update a Recommendation with the id
    DELETE /recommendation{id} -  Deletes a Recommendation with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE A RECOMMENDATION
    # ------------------------------------------------------------------
    @api.doc("get_recommendations")
    @api.response(404, "Recommendation not found")
    @api.marshal_with(recommendation_model)
    def get(self, recommendation_id):
        """
        Retrieve a single Recommendation

        This endpoint will return a Recommendation based on it's id
        """
        app.logger.info(
            "Request to Retrieve a recommendation with id [%s]", recommendation_id
        )
        recommendation = Recommendations.find(recommendation_id)
        if not recommendation:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Recommendation with id '{recommendation_id}' was not found.",
            )
        return recommendation.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING RECOMMENDATION
    # ------------------------------------------------------------------
    @api.doc("update_recommendations")
    @api.response(404, "Recommendation not found")
    @api.response(400, "The posted Recommendation data was not valid")
    @api.expect(recommendation_model)
    @api.marshal_with(recommendation_model)
    def put(self, recommendation_id):
        """
        Update a Recommendation

        This endpoint will update a Recommendation based the body that is posted
        """
        app.logger.info(
            "Request to Update a recommendation with id [%s]", recommendation_id
        )
        recommendation = Recommendations.find(recommendation_id)
        if not recommendation:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Recommendation with id '{recommendation_id}' was not found.",
            )
        app.logger.debug("Payload = %s", api.payload)
        data = api.payload
        recommendation.deserialize(data)
        recommendation.id = recommendation_id
        recommendation.update()
        return recommendation.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE A RECOMMENDATION
    # ------------------------------------------------------------------
    @api.doc("delete_recommendations")
    @api.response(204, "Recommendation deleted")
    def delete(self, recommendation_id):
        """
        Delete a Recommendation

        This endpoint will delete a Recommendation based the id specified in the path
        """
        app.logger.info(
            "Request to Delete a recommendation with id [%s]", recommendation_id
        )
        recommendation = Recommendations.find(recommendation_id)
        if recommendation:
            recommendation.delete()
            app.logger.info(
                "Recommendation with id [%s] was deleted", recommendation_id
            )

        return "", status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /recommendations
######################################################################
@api.route("/recommendations", strict_slashes=False)
class RecommendationCollection(Resource):
    """Handles all interactions with collections of Recommendations"""

    # ------------------------------------------------------------------
    # LIST ALL RECOMMENDATIONS
    # ------------------------------------------------------------------
    @api.doc("list_recommendations")
    @api.expect(recommendation_args, validate=True)
    @api.marshal_list_with(recommendation_model)
    def get(self):
        """Returns all of the Recommendations"""
        app.logger.info("Request to list Recommendations...")
        recommendations = []
        args = recommendation_args.parse_args()
        filters = filters_from_args(args)
        recommendations = Recommendations.find_by_filters(filters)
        app.logger.info("[%s] Recommendations returned", len(recommendations))
        results = [recommendation.serialize() for recommendation in recommendations]
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD A NEW PET
    # ------------------------------------------------------------------
    @api.doc("create_recommendations")
    @api.response(400, "The posted data was not valid")
    @api.expect(create_model)  # don't need to validate data in method
    @api.marshal_with(recommendation_model, code=201)
    def post(self):
        """
        Creates a Recommendation
        This endpoint will create a Recommendation based the data in the body that is posted
        """
        app.logger.info("Request to Create a Recommendation")
        recommendation = Recommendations()
        app.logger.debug("Payload = %s", api.payload)
        recommendation.deserialize(api.payload)
        recommendation.create()
        app.logger.info("Recommendation with new id [%s] created!", recommendation.id)
        location_url = api.url_for(
            RecommendationResource, recommendation_id=recommendation.id, _external=True
        )
        return (
            recommendation.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


#######################################################################
#  PATH: /recommendations/{id}/like
######################################################################
@api.route("/recommendations/<int:recommendation_id>/like")
@api.param("recommendation_id", "The Recommendation identifier")
class LikeResource(Resource):
    """Like action on a Recommendation"""

    @api.doc("like_recommendations")
    @api.response(404, "Recommendation not found")
    def put(self, recommendation_id):
        """
        Like a Recommendation

        This endpoint will increment like of a Recommendation by 1
        """
        app.logger.info(
            "Request to like a recommendation with id: %d", recommendation_id
        )
        recommendation = Recommendations.find(recommendation_id)
        if not recommendation:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Recommendation with id [{recommendation_id}] was not found.",
            )
        recommendation.like += 1
        recommendation.update()
        app.logger.info(
            "Recommendation with id [%s] has been liked!", recommendation.id
        )
        return recommendation.serialize(), status.HTTP_200_OK


#######################################################################
#  PATH: /recommendations/{id}/dislike
######################################################################
@api.route("/recommendations/<int:recommendation_id>/dislike")
@api.param("recommendation_id", "The Recommendation identifier")
class DislikeResource(Resource):
    """Dislike action on a Recommendation"""

    @api.doc("dislike_recommendations")
    @api.response(404, "Recommendation not found")
    def put(self, recommendation_id):
        """
        Dislike a Recommendation

        This endpoint will increment dislike of a Recommendation by 1
        """
        app.logger.info(
            "Request to dislike a recommendation with id: %d", recommendation_id
        )
        recommendation = Recommendations.find(recommendation_id)
        if not recommendation:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Recommendation with id [{recommendation_id}] was not found.",
            )
        recommendation.dislike += 1
        recommendation.update()
        app.logger.info(
            "Recommendation with id [%s] has been disliked!", recommendation.id
        )
        return recommendation.serialize(), status.HTTP_200_OK


# ######################################################################
# # LIST ALL RECOMMENDATIONS
# ######################################################################
# @app.route("/recommendations", methods=["GET"])
# def list_recommendations():
#     """Returns all of the recommendations"""
#     app.logger.info("Request for recommendation list")
#     # Utilize the general function find_by_filters
#     # Thus first parse the passed-in filters
#     filters = filters_from_args()
#     recommendations = Recommendations.find_by_filters(filters)
#     serialized_results = [
#         recommendation.serialize() for recommendation in recommendations
#     ]
#     app.logger.info("Returning %d recommendations", len(serialized_results))
#     return jsonify(serialized_results), status.HTTP_200_OK


######################################################################
# HELPER FUNCTIONS FOR LIST ROUTE
######################################################################
def parse_int_param(param_name):
    """Helper function to parse integer query parameters"""
    try:
        return int(request.args.get(param_name))
    except (ValueError, TypeError) as exc:
        app.logger.error("Invalid %s", param_name)
        raise BadRequest("Invalid data type: must be an integer") from exc


def validate_enum_param(param_name, value, valid_options):
    """Helper function to validate enum query parameters"""
    if value not in valid_options:
        app.logger.error("Invalid %s", param_name)
        raise BadRequest(f"Invalid {param_name}: must be one of {valid_options}")
    return value


def filters_from_args(args):
    """Helper function to build filters dictionary from parsed args with custom validation"""
    filters = {}
    if "product_id" in args and args["product_id"] is not None:
        filters["product_id"] = parse_int_param("product_id")  # Validate as integer
    if "recommended_id" in args and args["recommended_id"] is not None:
        filters["recommended_id"] = parse_int_param(
            "recommended_id"
        )  # Validate as integer
    if "page" in args and args["page"] is not None:
        filters["page"] = parse_int_param("page")  # Validate as integer
    if "limit" in args and args["limit"] is not None:
        filters["limit"] = parse_int_param("limit")  # Validate as integer
    if "recommendation_type" in args and args["recommendation_type"] is not None:
        filters["recommendation_type"] = validate_enum_param(
            "recommendation_type",
            args["recommendation_type"],
            ["cross-sell", "up-sell", "accessory"],
        )
    if "status" in args and args["status"] is not None:
        filters["status"] = validate_enum_param(
            "status",
            args["status"],
            ["active", "expired", "draft"],
        )
    if "sort_by" in args and args["sort_by"] is not None:
        filters["sort_by"] = args["sort_by"]  # No additional validation needed
    if "order" in args and args["order"] is not None:
        filters["order"] = args["order"]  # No additional validation needed
    return filters


# def filters_from_args():
#     """Helper function to build filters dictionary from query args"""
#     filters = {}
#     if "product_id" in request.args:
#         filters["product_id"] = parse_int_param("product_id")
#     if "recommended_id" in request.args:
#         filters["recommended_id"] = parse_int_param("recommended_id")
#     if "page" in request.args:
#         filters["page"] = parse_int_param("page")
#     if "limit" in request.args:
#         filters["limit"] = parse_int_param("limit")
#     if "recommendation_type" in request.args:
#         filters["recommendation_type"] = validate_enum_param(
#             "recommendation_type",
#             request.args.get("recommendation_type"),
#             ["cross-sell", "up-sell", "accessory"],
#         )
#     if "status" in request.args:
#         filters["status"] = validate_enum_param(
#             "status",
#             request.args.get("status"),
#             ["active", "expired", "draft"],
#         )
#     if "sort_by" in request.args:
#         filters["sort_by"] = request.args.get("sort_by")
#     if "order" in request.args:
#         filters["order"] = request.args.get("order")
#     return filters


# ######################################################################
# # CREATE A NEW RECOMMENDATION
# ######################################################################
# @app.route("/recommendations", methods=["POST"])
# def create_recommendations():
#     """
#     Create a Recommendation
#     This endpoint will create a Recommendation based the data in the body that is posted
#     """
#     app.logger.info("Request to Create a Recommendation...")
#     check_content_type("application/json")

#     try:
#         recommendation = Recommendations()
#         # Get the data from the request and deserialize it
#         data = request.get_json()
#         app.logger.info("Processing: %s", data)
#         recommendation.deserialize(data)

#         # Save the new Recommendation to the database
#         recommendation.create()
#     except DataValidationError as e:
#         app.logger.error("Data validation error: %s", str(e))
#         abort(status.HTTP_400_BAD_REQUEST, str(e))
#     except SQLAlchemyError as e:
#         app.logger.error("Database error: %s", str(e))
#         abort(status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error occurred")
#     except Exception as e:  # pylint: disable=broad-except
#         app.logger.error("Unexpected error: %s", str(e))
#         abort(status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred")

#     app.logger.info("Recommendation with new id [%s] saved!", recommendation.id)

#     # Return the location of the new Recommendation
#     location_url = url_for(
#         "get_recommendations", recommendation_id=recommendation.id, _external=True
#     )
#     # location_url = "/"
#     return (
#         jsonify(recommendation.serialize()),
#         status.HTTP_201_CREATED,
#         {"Location": location_url},
#     )


# ######################################################################
# # READ A RECOMMENDATION
# ######################################################################
# @app.route("/recommendations/<int:recommendation_id>", methods=["GET"])
# def get_recommendations(recommendation_id):
#     """
#     Retrieve a single Recommendation

#     This endpoint will return a Recommendation based on it's id
#     """
#     app.logger.info(
#         "Request to Retrieve a recommendation with id [%s]", recommendation_id
#     )

#     # Attempt to find the Recommendation and abort if not found
#     recommendation = Recommendations.find(recommendation_id)
#     if not recommendation:
#         abort(
#             status.HTTP_404_NOT_FOUND,
#             f"Recommendation with id '{recommendation_id}' was not found.",
#         )

#     app.logger.info("Returning recommendation: %s", recommendation.id)
#     return jsonify(recommendation.serialize()), status.HTTP_200_OK


# ######################################################################
# # DELETE A RECOMMENDATION
# ######################################################################
# @app.route("/recommendations/<int:recommendation_id>", methods=["DELETE"])
# def delete_recommendations(recommendation_id):
#     """
#     Delete a Recommendation
#     This endpoint will delete a Recommendation based the id specified in the path
#     """
#     app.logger.info(
#         "Request to Delete a recommendation with id [%s]", recommendation_id
#     )

#     # Find the recommendation by id
#     recommendation = Recommendations.find(recommendation_id)

#     if recommendation:
#         app.logger.info(
#             "Recommendation with ID: %d found. Deleting...", recommendation_id
#         )
#         try:
#             recommendation.delete()
#         except SQLAlchemyError as e:
#             app.logger.error("Database error while deleting: %s", str(e))
#             abort(status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error occurred")
#         except Exception as e:  # pylint: disable=broad-except
#             app.logger.error("Unexpected error: %s", str(e))
#             abort(status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred")
#     else:
#         app.logger.info(
#             "Recommendation with ID: %d not found. Returning 204 No Content.",
#             recommendation_id,
#         )

#     return {}, status.HTTP_204_NO_CONTENT


# ######################################################################
# # UPDATE A RECOMMENDATION
# ######################################################################
# @app.route("/recommendations/<int:recommendation_id>", methods=["PUT"])
# def update_recommendations(recommendation_id):
#     """
#     Update a Recommendation

#     This endpoint will update a Recommendation based on the posted data
#     """
#     app.logger.info(
#         "Request to Update a recommendation with id [%s]", recommendation_id
#     )
#     check_content_type("application/json")

#     # Find the recommendation by id
#     recommendation = Recommendations.find(recommendation_id)
#     if not recommendation:
#         abort(
#             status.HTTP_404_NOT_FOUND,
#             f"Recommendation with id '{recommendation_id}' was not found.",
#         )

#     # Get the data from the request and handle malformed JSON
#     try:
#         data = request.get_json()
#     except BadRequest as e:
#         app.logger.error("Invalid JSON format: %s", str(e))
#         abort(status.HTTP_400_BAD_REQUEST, "Invalid JSON format")

#     app.logger.info("Processing update for recommendation: %s", data)

#     try:
#         # Deserialize and update the recommendation
#         recommendation.deserialize(data)
#         recommendation.update()
#     except DataValidationError as e:
#         # Handle concurrent modification or other validation errors
#         app.logger.error("Data validation error: %s", str(e))
#         if "updated by another process" in str(e):
#             abort(
#                 status.HTTP_409_CONFLICT, "The record was updated by another process."
#             )
#         abort(status.HTTP_400_BAD_REQUEST, str(e))
#     except SQLAlchemyError as e:
#         app.logger.error("Database error: %s", str(e))
#         abort(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")
#     except Exception as e:  # pylint: disable=broad-except
#         app.logger.error("Unexpected error: %s", str(e))
#         abort(status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred")

#     app.logger.info("Recommendation with id [%s] updated!", recommendation.id)
#     return jsonify(recommendation.serialize()), status.HTTP_200_OK


# ######################################################################
# # LIKE A RECOMMENDATION
# ######################################################################
# @app.route("/recommendations/<int:recommendation_id>/like", methods=["PUT"])
# def like_recommendations(recommendation_id):
#     """Liking a recommendation adds 1 to like"""
#     app.logger.info("Request to like a recommendation with id: %d", recommendation_id)

#     # Attempt to find the Recommendation and abort if not found
#     recommendation = Recommendations.find(recommendation_id)
#     if not recommendation:
#         abort(
#             status.HTTP_404_NOT_FOUND,
#             f"Recommendation with id '{recommendation_id}' was not found.",
#         )

#     # At this point you would execute code to like the recommendation
#     # For the moment, we will add the like by 1

#     recommendation.like += 1
#     recommendation.update()

#     app.logger.info("Recommendation with ID: %d has been liked.", recommendation_id)
#     return recommendation.serialize(), status.HTTP_200_OK


# ######################################################################
# # DISLIKE A RECOMMENDATION
# ######################################################################
# @app.route("/recommendations/<int:recommendation_id>/dislike", methods=["PUT"])
# def dislike_recommendations(recommendation_id):
#     """Disliking a recommendation adds 1 to dislike"""
#     app.logger.info(
#         "Request to dislike a recommendation with id: %d", recommendation_id
#     )

#     # Attempt to find the Recommendation and abort if not found
#     recommendation = Recommendations.find(recommendation_id)
#     if not recommendation:
#         abort(
#             status.HTTP_404_NOT_FOUND,
#             f"Recommendation with id '{recommendation_id}' was not found.",
#         )

#     # At this point you would execute code to dislike the recommendation
#     # For the moment, we will add the dislike by 1

#     recommendation.dislike += 1
#     recommendation.update()

#     app.logger.info("Recommendation with ID: %d has been disliked.", recommendation_id)
#     return recommendation.serialize(), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


######################################################################
# Checks the ContentType of a request
######################################################################
# def check_content_type(content_type) -> None:
#     """Checks that the media type is correct"""
#     if "Content-Type" not in request.headers:
#         app.logger.error("No Content-Type specified.")
#         abort(
#             status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
#             f"Content-Type must be {content_type}",
#         )

#     if request.headers["Content-Type"] == content_type:
#         return

#     app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
#     abort(
#         status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
#         f"Content-Type must be {content_type}",
#     )
