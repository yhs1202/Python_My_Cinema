import boto3
import os

def compare_faces(sourceFile, targetFile):
    result = ""
    client = boto3.client('rekognition')
    imageSource = open(sourceFile, 'rb')
    imageTarget = open(targetFile, 'rb')
    response = client.compare_faces(SimilarityThreshold=0,
                                    SourceImage={'Bytes': imageSource.read()},
                                    TargetImage={'Bytes': imageTarget.read()})
    for faceMatch in response['FaceMatches']:
        position = faceMatch['Face']['BoundingBox']
        similarity = faceMatch['Similarity']
        result += f"동일 인물일 확률 : {similarity:.2f}%\n"
        result += "<br/>"
    imageSource.close()
    imageTarget.close()
    return result

def detect_labels_local_file(photo):
    client=boto3.client('rekognition')
    with open(photo, 'rb') as image:
        response = client.detect_labels(Image={'Bytes': image.read()})
        
    result = []
    for label in response['Labels']:
        name = label['Name']
        confidence = label['Confidence']
        txt = f"{name} -> ({confidence:.2f}%)"
        result.append(txt)
    return "<br/>".join((map(str, result)))

def main():
    photo= os.path.join("./", "../") + 'cc.jpg'      # Replace with your image file path
    if not os.path.exists(photo):
        print("File does not exist.")
        return
    label_count=detect_labels_local_file(photo)
    print("Labels detected: " + str(label_count))

if __name__ == "__main__":
    main()