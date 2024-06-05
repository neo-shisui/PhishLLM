import os

from models.ranking_model.train import *
from models.ranking_model.torchattacks.attacks.fgsm import FGSM
from models.ranking_model.torchattacks.attacks.bim import BIM
from models.ranking_model.torchattacks.attacks.deepfool import DeepFool
from models.ranking_model.torchattacks.attacks.protect import *
import math
from tldextract import tldextract
os.environ['CUDA_VISIBLE_DEVICES'] = '3'

def tester_rank(model, test_dataset, device, protect_enabled, attack_method, adv_attack=True, image_save_dir=None):
    total = 0
    perturb_correct = 0

    df = pd.DataFrame({'url': test_dataset.urls,
                       'path': test_dataset.img_paths,
                       'label': test_dataset.labels})
    grp = df.groupby('url')
    grp = dict(list(grp), keys=lambda x: x[0])  # {url: List[dom_path, save_path]}

    for url, data in tqdm(grp.items()):
        torch.cuda.empty_cache()
        try:
            img_paths = data.path
            labels = data.label
        except:
            continue
        labels = torch.tensor(np.asarray(labels))
        images = []
        for path in img_paths:
            img_process = preprocess(Image.open(path))
            images.append(img_process)

        if (labels == 1).sum().item():  # has login button
            total += 1
        else:
            continue

        images = torch.stack(images).to(device)
        if adv_attack:
            # adversary attack
            target_labels = torch.zeros_like(labels)
            target_labels = target_labels.long().to(device)

            if protect_enabled:
                protect_act(model.visual)
                protect_resnetblock(model.visual)
                model = model.to(device)
            if attack_method == 'DeepFool':
                attack_cls = DeepFool(model, device=device)
            elif attack_method == 'FGSM':
                attack_cls = FGSM(model, device=device)
            elif attack_method == 'BIM':
                attack_cls = BIM(model, device=device)
            adv_images = attack_cls(images, labels, target_labels)
            images.detach()
            adv_images.detach()
            del attack_cls

        if image_save_dir and ((labels == 1).sum().item())>0:
            os.makedirs(image_save_dir, exist_ok=True)
            plt.figure(figsize=(10, 4))
            # Display original image
            plt.subplot(2, 1, 1)
            plt.imshow(images.detach()[torch.where(labels==1)[0].item()].permute(1, 2, 0).cpu().numpy())
            plt.title("Original")
            plt.axis('off')
            # Display adversarial image
            plt.subplot(2, 1, 2)
            plt.imshow(adv_images.detach()[torch.where(labels==1)[0].item()].permute(1, 2, 0).cpu().numpy())
            plt.title("Adversarial")
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(os.path.join(image_save_dir, tldextract.extract(url).domain+'.png'))

        # perturbed prediction
        del model
        model, _ = clip.load("ViT-B/32", device=device)
        model.load_state_dict(torch.load("./checkpoints/epoch4_model.pt"))
        model = model.to(device)
        freeze_params(model)

        texts = clip.tokenize(["not a login button", "a login button"]).to(device)
        with torch.no_grad():
            if adv_attack:
                logits_per_image, logits_per_text = model(adv_images, texts)
            else:
                logits_per_image, logits_per_text = model(images, texts)

        probs = logits_per_image.softmax(dim=-1)  # (N, C)
        conf = probs[torch.arange(probs.shape[0]), 1]  # take the confidence (N, 1)
        _, ind = torch.topk(conf, min(1, len(conf)))  # top1 index

        if (labels[ind] == 1).sum().item():  # has login button and it is reported
            perturb_correct += 1

        print(f"After attack correct count = {perturb_correct}, Total = {total}, Recall@K = {perturb_correct/total}")

    print(f"After attack correct count = {perturb_correct}, Total = {total}, Recall@K = {perturb_correct/total}")


if __name__ == '__main__':
    protect_enabled = False # protect or not
    attack_method = 'FGSM'
    assert attack_method in ['DeepFool', 'FGSM', 'BIM']

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    # https://github.com/openai/CLIP/issues/57
    if device == "cpu":
        model.float()

    test_dataset = ButtonDataset(annot_path='./datasets/alexa_login_test.txt',
                                 root='./datasets/alexa_login',
                                 preprocess=preprocess)
    test_dataloader = DataLoader(test_dataset, batch_size=1, shuffle=False)

    state_dict = torch.load("./checkpoints/epoch{}_model.pt".format(4))
    model.load_state_dict(state_dict)

    if protect_enabled:
        protect_act(model.visual) #
        protect_resnetblock(model.visual)
    model = model.to(device)
    freeze_params(model)

    tester_rank(model, test_dataset, device, protect_enabled=protect_enabled, attack_method=attack_method,
                image_save_dir='./ranking_model/test_case')

    # FGSM: After attack correct count = 210, Total = 321, Recall@K = 0.6542056074766355
    # BIM (iterative FGSM, but gradually increasing the perturbation magnitude) After attack correct count = 28, Total = 321, Recall@K = 0.08722741433021806
    # DeepFool After attack correct count = 10, Total = 321, Recall@K = 0.03115264797507788





