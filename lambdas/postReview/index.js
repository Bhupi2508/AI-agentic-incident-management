exports.handler = async (event) => {
  console.log("Post-incident review", event);
  return { status: "reviewed", incidentId: event.incidentId };
};