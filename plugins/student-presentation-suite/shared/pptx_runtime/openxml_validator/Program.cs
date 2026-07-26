using System.Text.Json;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Validation;

const int MaximumValidationErrors = 1000;

if (args.Length != 1)
{
    Console.Error.WriteLine("usage: OpenXmlValidator <presentation.pptx>");
    return 64;
}

var source = Path.GetFullPath(args[0]);
try
{
    using var document = PresentationDocument.Open(source, false);
    var validator = new OpenXmlValidator(FileFormatVersions.Microsoft365)
    {
        MaxNumberOfErrors = MaximumValidationErrors,
    };
    var errors = validator.Validate(document).Select(error => new
    {
        id = error.Id ?? "OpenXmlSchema",
        description = error.Description ?? "Open XML schema validation failed",
        error_type = error.ErrorType.ToString(),
        part = error.Part?.Uri.ToString(),
        path = error.Path?.XPath,
        node = error.Node?.LocalName,
        related_node = error.RelatedNode?.LocalName,
    }).ToArray();
    Console.WriteLine(JsonSerializer.Serialize(new
    {
        ok = errors.Length == 0,
        engine = "DocumentFormat.OpenXml",
        engine_version = typeof(OpenXmlValidator).Assembly.GetName().Version?.ToString(),
        target = FileFormatVersions.Microsoft365.ToString(),
        max_errors = MaximumValidationErrors,
        truncated = errors.Length >= MaximumValidationErrors,
        errors,
    }));
    return errors.Length == 0 ? 0 : 1;
}
catch (Exception exception)
{
    Console.WriteLine(JsonSerializer.Serialize(new
    {
        ok = false,
        engine = "DocumentFormat.OpenXml",
        fatal = true,
        error_type = exception.GetType().Name,
        description = exception.Message,
    }));
    return 2;
}
